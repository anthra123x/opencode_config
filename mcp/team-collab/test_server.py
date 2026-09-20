#!/usr/bin/env python3
"""
Unit tests for team-collab MCP server with project scoping and handoffs.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["OPENCODE_TEAM_DB"] = temp_db.name

import server

class TestTeamCollabServer(unittest.TestCase):
    def setUp(self):
        conn = server.get_db()
        with conn:
            conn.execute("DELETE FROM team_messages")
            conn.execute("DELETE FROM team_agents")
            conn.execute("DELETE FROM team_tasks")
            conn.execute("DELETE FROM team_artifacts")

    def tearDown(self):
        pass

    def test_broadcast_and_feed_project_scoped(self):
        res = server.tool_team_broadcast({
            "sender": "backend",
            "message": "Auth API endpoints implemented with refresh tokens.",
            "category": "handoff",
            "priority": "high",
            "project": "project-alpha"
        })
        self.assertIn("Broadcasted message from @backend", res)
        self.assertIn("project-alpha", res)

        feed = server.tool_team_read_feed({"limit": 5, "project": "project-alpha"})
        self.assertIn("@backend", feed)
        self.assertIn("Auth API endpoints", feed)

        # Feed for other project should not show alpha's message
        other_feed = server.tool_team_read_feed({"limit": 5, "project": "project-beta"})
        self.assertNotIn("Auth API endpoints", other_feed)

    def test_handoff_workflow(self):
        # Post task
        post_res = server.tool_team_post_task({
            "title": "Build Auth System",
            "assigned_to": "backend",
            "project": "project-alpha"
        })
        self.assertIn("Task #1 posted", post_res)

        # Handoff from backend to frontend
        handoff_res = server.tool_team_handoff({
            "from_agent": "backend",
            "to_agent": "frontend",
            "task_id": 1,
            "notes": "Endpoints POST /api/auth ready. Artifact auth-spec shared.",
            "artifact_key": "auth-spec",
            "project": "project-alpha"
        })
        self.assertIn("Handoff completed in [project-alpha]", handoff_res)

        # Verify frontend is working and backend is idle
        status_res = server.tool_team_get_status({"project": "project-alpha"})
        self.assertIn("@frontend", status_res)
        self.assertIn("WORKING", status_res)

if __name__ == "__main__":
    unittest.main()
