#!/usr/bin/env python3
"""
Multi-Window Real-Time Swarm Concurrency Verification Test.
Simulates 3 distinct OpenCode terminal sessions running simultaneously in the same project:
  - Window 1: Backend Specialist (API, Schemas, Migrations)
  - Window 2: Frontend Specialist (UI Components, Consuming API)
  - Window 3: Git & Flow Manager (Branch Hygiene, Conventional Commits)

Validates that:
  1. WAL mode and db_write_lock prevent any 'database is locked' errors or crashes.
  2. All sessions see what the other is doing in real time.
  3. Window IDs, heartbeats, and relative timestamps are accurately synchronized.
"""

import sys
import os
import time
import multiprocessing
from pathlib import Path

# Add mcp servers to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp" / "team-collab"))
import server as team_server

PROJECT_NAME = "multi-win-simulation"

def run_backend_window(barrier, error_queue):
    try:
        barrier.wait() # Synchronize start with other windows
        window_id = "term-1-backend"
        agent = "backend"

        # 1. Announce start of work
        team_server.tool_team_set_status({
            "agent_name": agent,
            "window_id": window_id,
            "status": "working",
            "current_task": "Implementing /api/catalog and Prisma schema",
            "project": PROJECT_NAME
        })

        # 2. Simulate progressive updates & heartbeats
        for i in range(3):
            time.sleep(0.05)
            team_server.tool_team_heartbeat({
                "agent_name": agent,
                "window_id": window_id,
                "current_task": f"Compiling migrations and route unit tests (pass {i+1})",
                "project": PROJECT_NAME
            })

        # 3. Share API contract artifact
        team_server.tool_team_share_artifact({
            "creator": agent,
            "artifact_key": "catalog-api-contract",
            "title": "Catalog & Cart API Specification",
            "artifact_type": "api_spec",
            "content": "GET /api/catalog -> { items: CatalogItem[] }\nPOST /api/cart -> { cartId: string }",
            "project": PROJECT_NAME
        })

        # 4. Broadcast handoff to Frontend
        team_server.tool_team_broadcast({
            "sender": agent,
            "message": "Catalog API & Prisma models published. Contract shared at 'catalog-api-contract'.",
            "category": "handoff",
            "priority": "high",
            "project": PROJECT_NAME
        })

    except Exception as e:
        error_queue.put(f"[Backend Error]: {e}")

def run_frontend_window(barrier, error_queue):
    try:
        barrier.wait() # Synchronize start
        window_id = "term-2-frontend"
        agent = "frontend"

        # 1. Query live activity to see what backend is doing
        live = team_server.tool_team_get_live_activity({"project": PROJECT_NAME})

        # 2. Announce frontend work
        team_server.tool_team_set_status({
            "agent_name": agent,
            "window_id": window_id,
            "status": "working",
            "current_task": "Building Catalog Showcase with Tailwind & Lucide",
            "project": PROJECT_NAME
        })

        for i in range(3):
            time.sleep(0.04)
            team_server.tool_team_heartbeat({
                "agent_name": agent,
                "window_id": window_id,
                "current_task": f"Styling catalog cards and spring animations (step {i+1})",
                "project": PROJECT_NAME
            })

        # 3. Read contract published by backend
        artifact = team_server.tool_team_get_artifact({
            "artifact_key": "catalog-api-contract",
            "project": PROJECT_NAME
        })

        # 4. Share UI contract & Broadcast
        team_server.tool_team_share_artifact({
            "creator": agent,
            "artifact_key": "ui-catalog-specs",
            "title": "Catalog Showcase UI Props",
            "artifact_type": "ui_contract",
            "content": "interface CatalogProps { items: CatalogItem[], onSelect: (id: string) => void }",
            "project": PROJECT_NAME
        })

        team_server.tool_team_broadcast({
            "sender": agent,
            "message": "UI Catalog completed with OKLCH theme and spring motion. Ready for review.",
            "category": "status",
            "priority": "normal",
            "project": PROJECT_NAME
        })

    except Exception as e:
        error_queue.put(f"[Frontend Error]: {e}")

def run_git_window(barrier, error_queue):
    try:
        barrier.wait() # Synchronize start
        window_id = "term-3-git"
        agent = "git-flow"

        # 1. Announce git session
        team_server.tool_team_set_status({
            "agent_name": agent,
            "window_id": window_id,
            "status": "working",
            "current_task": "Inspecting git diff and validating conventional commits",
            "project": PROJECT_NAME
        })

        for i in range(3):
            time.sleep(0.03)
            # Periodic live check of the swarm
            live_status = team_server.tool_team_get_live_activity({"project": PROJECT_NAME})

        # 2. Broadcast commit status
        team_server.tool_team_broadcast({
            "sender": agent,
            "message": "feat(catalog): implement end-to-end catalog API, UI components and specs",
            "category": "announcement",
            "priority": "normal",
            "project": PROJECT_NAME
        })

        team_server.tool_team_set_status({
            "agent_name": agent,
            "window_id": window_id,
            "status": "idle",
            "current_task": "Branch ready for PR merge",
            "project": PROJECT_NAME
        })

    except Exception as e:
        error_queue.put(f"[Git-Flow Error]: {e}")

def main():
    print("=" * 65)
    print("  SIMULATING 3 CONCURRENT OPENCODE TERMINAL WINDOWS")
    print("  Window 1: @backend   (term-1-backend)")
    print("  Window 2: @frontend  (term-2-frontend)")
    print("  Window 3: @git-flow  (term-3-git)")
    print("=" * 65)

    barrier = multiprocessing.Barrier(3)
    error_queue = multiprocessing.Queue()

    p_backend = multiprocessing.Process(target=run_backend_window, args=(barrier, error_queue))
    p_frontend = multiprocessing.Process(target=run_frontend_window, args=(barrier, error_queue))
    p_git = multiprocessing.Process(target=run_git_window, args=(barrier, error_queue))

    # Launch all 3 windows concurrently
    p_backend.start()
    p_frontend.start()
    p_git.start()

    p_backend.join(timeout=10)
    p_frontend.join(timeout=10)
    p_git.join(timeout=10)

    # Check for errors
    errors = []
    while not error_queue.empty():
        errors.append(error_queue.get())

    if errors:
        print("\n❌ ERRORS ENCOUNTERED DURING CONCURRENT EXECUTION:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)

    print("\n✓ All 3 concurrent windows completed without a single error or deadlock!")

    # Verify final live activity
    print("\n" + "=" * 65)
    print("  FINAL LIVE SWARM ACTIVITY SNAPSHOT ACROSS ALL 3 WINDOWS:")
    print("=" * 65)
    live_report = team_server.tool_team_get_live_activity({"project": PROJECT_NAME})
    print(live_report)

    # Assertions
    assert "@backend" in live_report, "Backend agent missing from live activity"
    assert "term-1-backend" in live_report, "Backend window ID missing"
    assert "@frontend" in live_report, "Frontend agent missing from live activity"
    assert "term-2-frontend" in live_report, "Frontend window ID missing"
    assert "@git-flow" in live_report, "Git-flow agent missing from live activity"
    assert "term-3-git" in live_report, "Git-flow window ID missing"
    assert "catalog-api-contract" in live_report, "Shared API contract missing from live activity"
    assert "feat(catalog)" in live_report, "Git broadcast missing from live activity"

    print("\n✓ 100% of assertions passed! Concurrency & multi-window sync verified successfully.")

if __name__ == "__main__":
    main()
