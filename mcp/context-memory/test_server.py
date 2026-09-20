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

if __name__ == "__main__":
    unittest.main()
