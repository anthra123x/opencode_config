#!/usr/bin/env python3
"""
Unit tests for Swarm Live Tester MCP server.
"""

import os
import sys
import tempfile
import unittest
import http.server
import threading
from pathlib import Path

# Setup temporary databases
temp_tester_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_sentinel_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_team_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)

os.environ["OPENCODE_TESTER_DB"] = temp_tester_db.name
os.environ["OPENCODE_SENTINEL_DB"] = temp_sentinel_db.name
os.environ["OPENCODE_TEAM_DB"] = temp_team_db.name

import server

class MockHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "app": "live-tester-test"}')

    def log_message(self, format, *args):
        pass

class TestSwarmTesterServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start mock HTTP server
        cls.httpd = http.server.HTTPServer(("127.0.0.1", 0), MockHandler)
        cls.port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        conn = server.get_db()
        try:
            with conn:
                conn.execute("DELETE FROM tester_runs")
                conn.execute("DELETE FROM component_checks")
                conn.execute("DELETE FROM endpoint_probes")
        finally:
            conn.close()

    def test_run_suite_and_parser(self):
        # Run test on context-memory unit test
        res = server.tool_tester_run_suite({
            "project": "test-project",
            "path": "mcp/context-memory/test_server.py",
            "runner": "unittest"
        })
        self.assertIn("Swarm Live Tester — Test Suite Execution", res)
        self.assertIn("Status: PASS", res)
        self.assertIn("passed", res)

        # Verify recorded in DB
        conn = server.get_db()
        try:
            row = conn.execute("SELECT status, passed, total_tests FROM tester_runs WHERE project = 'test-project'").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "PASS")
            self.assertGreater(row["passed"], 0)
        finally:
            conn.close()

    def test_probe_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/api/health"
        res = server.tool_tester_probe_endpoint({
            "url": url,
            "method": "GET",
            "expected_status": 200,
            "project": "test-project"
        })
        self.assertIn("[PASS]", res)
        self.assertIn("Status: 200", res)

        # Probe non-existent port (should record FAIL)
        fail_res = server.tool_tester_probe_endpoint({
            "url": "http://127.0.0.1:59999/api/unknown",
            "method": "GET",
            "expected_status": 200,
            "project": "test-project"
        })
        self.assertIn("[FAIL]", fail_res)

        # Verify probe count in DB
        conn = server.get_db()
        try:
            probes = conn.execute("SELECT COUNT(*) FROM endpoint_probes WHERE project = 'test-project'").fetchone()[0]
            self.assertEqual(probes, 2)
        finally:
            conn.close()

    def test_verify_component_python_and_js(self):
        # 1. Verify valid python component
        valid_py = server.tool_tester_verify_component({
            "file_path": "mcp/context-memory/server.py",
            "project": "test-project"
        })
        self.assertIn("Python AST syntax parse clean", valid_py)

        # 2. Verify temporary python with syntax error
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def broken_syntax(:\n    pass\n")
            broken_path = f.name

        try:
            broken_res = server.tool_tester_verify_component({
                "file_path": broken_path,
                "project": "test-project"
            })
            self.assertIn("Python SyntaxError", broken_res)
            self.assertIn("[FAIL]", broken_res)
        finally:
            try:
                os.remove(broken_path)
            except Exception:
                pass

    def test_live_health_scorecard(self):
        # Run a test and a probe first
        server.tool_tester_probe_endpoint({
            "url": f"http://127.0.0.1:{self.port}/",
            "method": "GET",
            "expected_status": 200,
            "project": "health-project"
        })
        server.tool_tester_run_suite({
            "project": "health-project",
            "path": "mcp/context-memory/test_server.py",
            "runner": "unittest"
        })

        health_res = server.tool_tester_get_live_health({"project": "health-project"})
        self.assertIn("Swarm Live Tester — Real-Time Health Scorecard", health_res)
        self.assertIn("HEALTHY", health_res)
        self.assertIn("Recent Test Runs", health_res)
        self.assertIn("Active Endpoint Probes", health_res)

    def test_sync_with_sentinel(self):
        # Populate passing test run
        server.tool_tester_run_suite({
            "project": "sync-project",
            "path": "mcp/context-memory/test_server.py",
            "runner": "unittest"
        })

        sync_res = server.tool_tester_sync_with_sentinel({"project": "sync-project"})
        self.assertIn("Synchronized with Swarm Sentinel", sync_res)

if __name__ == "__main__":
    unittest.main()
