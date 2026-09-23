#!/usr/bin/env python3
"""
Unit tests for context-memory MCP server with project scoping and bootstrap.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["OPENCODE_MEMORY_DB"] = temp_db.name

import server

class TestContextMemoryServer(unittest.TestCase):
    def setUp(self):
        conn = server.get_db()
        with conn:
            conn.execute("DELETE FROM memories")
            try:
                conn.execute("DELETE FROM memories_fts")
            except Exception:
                pass

    def tearDown(self):
        pass

    def test_remember_and_recall_scoped(self):
        server.tool_remember({
            "key": "jwt-pattern",
            "content": "Use RS256 algorithm.",
            "category": "architecture",
            "project": "app-x"
        })

        # Recall in same project
        res_x = server.tool_recall({"query": "RS256", "project": "app-x"})
        self.assertIn("jwt-pattern", res_x)

    def test_session_bootstrap(self):
        server.tool_remember({
            "key": "app-x-tech-stack",
            "content": "Next.js 15, Tailwind v4, PostgreSQL",
            "category": "architecture",
            "project": "app-x"
        })

        bootstrap = server.tool_get_session_bootstrap({"project": "app-x"})
        self.assertIn("Next.js 15", bootstrap)
        self.assertIn("Team Board Status", bootstrap)

    def test_checkpoint_session_and_retrieval(self):
        res = server.tool_checkpoint_session({
            "project": "app-x",
            "summary": "Completed authentication module and JWT validation middleware",
            "decisions": "Adopted RSA-256 with key rotation",
            "files_modified": "src/lib/auth.ts, src/middleware.ts",
            "next_steps": "Write E2E tests for login flow"
        })
        self.assertIn("Milestone Checkpoint persisted", res)

        checkpoint = server.tool_get_session_checkpoint({"project": "app-x"})
        self.assertIn("LATEST SESSION CHECKPOINT", checkpoint)
        self.assertIn("Completed authentication module", checkpoint)
        self.assertIn("Adopted RSA-256", checkpoint)
        self.assertIn("Write E2E tests", checkpoint)

    def test_auto_sync_project_memory(self):
        with tempfile.TemporaryDirectory() as td:
            pkg = Path(td) / "package.json"
            pkg.write_text('{"dependencies": {"next": "15.0", "react": "19.0"}}', encoding="utf-8")

            res = server.tool_auto_sync_project_memory({
                "project": "temp-app",
                "workspace_dir": td
            })
            self.assertIn("Auto-synced persistent memory", res)

            # Check that memories exist
            mem = server.tool_recall({"query": "Next.js", "project": "temp-app"})
            self.assertIn("tech-stack", mem)
            self.assertIn("React", mem)

    def test_auto_checkpoint_trigger(self):
        res1 = server.tool_trigger_auto_checkpoint({
            "project": "auto-test-app",
            "event_type": "task_completed",
            "details": "User authentication endpoints implemented"
        })
        self.assertIn("Milestone Checkpoint persisted", res1)

        # Immediate follow-up should be debounced
        res2 = server.tool_trigger_auto_checkpoint({
            "project": "auto-test-app",
            "event_type": "artifact_published",
            "details": "Another event immediately"
        })
        self.assertIn("Debounced", res2)

        # Checkpoint is retrievable
        chk = server.tool_get_session_checkpoint({"project": "auto-test-app"})
        self.assertIn("User authentication endpoints", chk)

if __name__ == "__main__":
    unittest.main()

