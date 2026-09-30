#!/usr/bin/env python3
"""
Unit tests for Swarm Sentinel MCP Server.
Verifies:
  1. Default rules exist and can be retrieved.
  2. Subagent deliverable audit passes clean work and rejects infractions.
  3. Secret detection triggers critical security violation.
  4. Manual violation recording, resolution, and compliance reporting.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["OPENCODE_SENTINEL_DB"] = temp_db.name

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server

class TestSwarmSentinelServer(unittest.TestCase):
    def setUp(self):
        conn = server.get_db()
        with conn:
            conn.execute("DELETE FROM sentinel_audits")
            conn.execute("DELETE FROM sentinel_violations")

    def test_get_rules(self):
        rules_text = server.tool_sentinel_get_rules({"agent_name": "backend"})
        self.assertIn("TDD-001", rules_text)
        self.assertIn("SEC-001", rules_text)

    def test_audit_clean_backend_deliverable(self):
        res = server.tool_sentinel_audit_task({
            "agent_name": "backend",
            "task_title": "Build Product Catalog REST Endpoints",
            "files_or_diff": "src/controllers/products.ts, tests/api/products.test.ts",
            "test_summary": "6 tests passing, 89% coverage verified",
            "artifact_key": "catalog-api-spec",
            "project": "test-project"
        })
        self.assertIn("APPROVED", res)
        self.assertIn("100/100", res)

    def test_audit_detects_secrets(self):
        res = server.tool_sentinel_audit_task({
            "agent_name": "backend",
            "task_title": "Add third-party payment integration",
            "files_or_diff": 'const apiKey = "sk-abcdef12345678901234567890123456";',
            "test_summary": "all tests pass",
            "project": "test-project"
        })
        self.assertIn("REJECTED", res)
        self.assertIn("SEC-001", res)

    def test_record_and_resolve_violation(self):
        rec_res = server.tool_sentinel_record_violation({
            "agent_name": "git-flow",
            "rule_code": "GIT-001",
            "details": "Pushed commit with unformatted message 'wip'",
            "severity": "medium",
            "project": "test-project"
        })
        self.assertIn("Violation #", rec_res)

        # Compliance check should show violation
        comp_res = server.tool_sentinel_verify_compliance({"project": "test-project"})
        self.assertIn("Active Open Violations: 1", comp_res)

        # Resolve violation
        conn = server.get_db()
        v = conn.execute("SELECT id FROM sentinel_violations LIMIT 1").fetchone()
        self.assertIsNotNone(v)

        res_res = server.tool_sentinel_resolve_violation({
            "violation_id": v["id"],
            "resolution_notes": "Squashed and reworded commit to feat(auth): add login form",
            "project": "test-project"
        })
        self.assertIn("RESOLVED", res_res)

    def test_compliance_report(self):
        rep = server.tool_sentinel_get_compliance_report({"project": "test-project"})
        self.assertIn("Sentinel Compliance Certification Report", rep)
        self.assertIn("Quality Grade", rep)

if __name__ == "__main__":
    unittest.main()
