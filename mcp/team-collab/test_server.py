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

    def test_live_activity_and_heartbeat(self):
        # Window 1: backend heartbeat
        hb1 = server.tool_team_heartbeat({
            "agent_name": "backend",
            "window_id": "window-1-backend",
            "current_task": "Implementing /api/checkout",
            "project": "project-ecommerce"
        })
        self.assertIn("Heartbeat acknowledged for @backend", hb1)

        # Window 2: frontend heartbeat
        hb2 = server.tool_team_heartbeat({
            "agent_name": "frontend",
            "window_id": "window-2-frontend",
            "current_task": "Building Cart Modal Component",
            "project": "project-ecommerce"
        })
        self.assertIn("Heartbeat acknowledged for @frontend", hb2)

        # Window 3: git-flow status
        server.tool_team_set_status({
            "agent_name": "git-flow",
            "window_id": "window-3-git",
            "status": "working",
            "current_task": "Rebasing feature/cart branch",
            "project": "project-ecommerce"
        })

        # Post a broadcast
        server.tool_team_broadcast({
            "sender": "backend",
            "message": "Checkout API spec ready",
            "project": "project-ecommerce"
        })

        # Check live activity snapshot
        live = server.tool_team_get_live_activity({"project": "project-ecommerce"})
        self.assertIn("@backend", live)
        self.assertIn("window-1-backend", live)
        self.assertIn("@frontend", live)
        self.assertIn("window-2-frontend", live)
        self.assertIn("@git-flow", live)
        self.assertIn("window-3-git", live)
        self.assertIn("ACTIVE", live)
        self.assertIn("Checkout API spec ready", live)

    def test_multi_window_concurrency(self):
        import concurrent.futures

        def write_action(worker_id):
            agent = ["backend", "frontend", "git-flow", "qa-auditor"][worker_id % 4]
            window = f"win-{worker_id}"
            server.tool_team_heartbeat({
                "agent_name": f"{agent}-{worker_id}",
                "window_id": window,
                "current_task": f"Task from worker {worker_id}",
                "project": "concurrency-test"
            })
            server.tool_team_broadcast({
                "sender": f"{agent}-{worker_id}",
                "message": f"Broadcast message {worker_id}",
                "project": "concurrency-test"
            })
            server.tool_team_post_task({
                "title": f"Task #{worker_id}",
                "assigned_to": agent,
                "project": "concurrency-test"
            })
            return True

        # Run 20 concurrent operations across 8 worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(write_action, range(20)))

        self.assertEqual(len(results), 20)
        self.assertTrue(all(results))

        # Check that feed and tasks were all written safely without SQLite deadlock
        feed = server.tool_team_read_feed({"limit": 50, "project": "concurrency-test"})
        self.assertIn("=== Team Activity Feed [concurrency-test]", feed)

    def test_reactive_cross_agent_trigger(self):
        # Backend shares API spec contract
        share_res = server.tool_team_share_artifact({
            "creator": "backend",
            "artifact_key": "cart-api-contract",
            "title": "Cart & Checkout REST API Spec",
            "artifact_type": "api_spec",
            "content": "POST /api/v1/cart { items: [] }",
            "project": "project-reactive"
        })
        self.assertIn("Reactive trigger dispatched to @frontend", share_res)

        # Check that frontend has pending triggers
        triggers_res = server.tool_team_check_triggers({
            "agent_name": "frontend",
            "project": "project-reactive",
            "claim": True
        })
        self.assertIn("cart-api-contract", triggers_res)
        self.assertIn("claimed", triggers_res)

        # Verify frontend status is working on trigger
        status_res = server.tool_team_get_status({"project": "project-reactive"})
        self.assertIn("@frontend", status_res)
        self.assertIn("WORKING", status_res)

    def test_project_isolated_agent_status(self):
        # Backend working in Project 1
        server.tool_team_set_status({
            "agent_name": "backend",
            "status": "working",
            "current_task": "Building DB models in Project 1",
            "project": "project-1"
        })

        # Backend idle in Project 2
        server.tool_team_set_status({
            "agent_name": "backend",
            "status": "idle",
            "current_task": "",
            "project": "project-2"
        })

        # Project 1 should still show backend working
        st1 = server.tool_team_get_status({"project": "project-1"})
        self.assertIn("WORKING", st1)
        self.assertIn("Building DB models in Project 1", st1)

        # Project 2 should show backend idle
        st2 = server.tool_team_get_status({"project": "project-2"})
        self.assertIn("IDLE", st2)

    def test_task_completion_sets_agent_idle(self):
        # Post and claim task for qa-auditor
        server.tool_team_post_task({
            "title": "Verify OWASP and Test Coverage",
            "assigned_to": "qa-auditor",
            "project": "project-audit"
        })
        cur = server.get_db().execute("SELECT id FROM team_tasks WHERE project = 'project-audit' ORDER BY id DESC LIMIT 1")
        task_id = cur.fetchone()["id"]

        server.tool_team_claim_task({
            "task_id": task_id,
            "agent_name": "qa-auditor",
            "project": "project-audit"
        })
        st_working = server.tool_team_get_status({"project": "project-audit"})
        self.assertIn("WORKING", st_working)

        # Mark task completed
        update_res = server.tool_team_update_task({
            "task_id": task_id,
            "status": "completed",
            "notes": "100% tests passing, zero vulnerabilities"
        })
        self.assertIn("COMPLETED", update_res)

        # Verify qa-auditor automatically transitioned to IDLE
        st_idle = server.tool_team_get_status({"project": "project-audit"})
        self.assertIn("IDLE", st_idle)

if __name__ == "__main__":
    unittest.main()

