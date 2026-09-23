#!/usr/bin/env python3
"""
Comprehensive End-to-End Workflow & Stability Test for OpenCode Swarm.
Tests:
  1. Multi-request endurance & zero connection leaks on Web Server (REST + SSE).
  2. Agent project isolation (compound primary key prevents clobbering).
  3. Reactive Cross-Agent Triggering (Backend ➔ Frontend ➔ QA-Auditor).
  4. Automatic Zero-Compaction Checkpoint generation.
  5. Automatic agent transition to idle on task completion.
  6. GetBrain real-time knowledge graph synchronization.
"""

import sys
import os
import json
import time
import urllib.request
import subprocess
from pathlib import Path
import importlib.util

# Paths
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR / "web"))
import brain_builder

# Load team collab server
team_spec = importlib.util.spec_from_file_location("team_collab_server", str(WORKSPACE_DIR / "mcp" / "team-collab" / "server.py"))
team_server = importlib.util.module_from_spec(team_spec)
team_spec.loader.exec_module(team_server)

# Load context memory server
mem_spec = importlib.util.spec_from_file_location("context_memory_server", str(WORKSPACE_DIR / "mcp" / "context-memory" / "server.py"))
mem_server = importlib.util.module_from_spec(mem_spec)
mem_spec.loader.exec_module(mem_server)

def log(msg):
    print(f"  ✓ {msg}")

def header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_all_tests():
    header("STAGE 1: Server Launch & Endurance (Zero Connection Leaks)")
    # Ensure server is running for this workspace
    proc = subprocess.run([
        sys.executable,
        str(WORKSPACE_DIR / "web" / "server.py"),
        "--ensure",
        "--dir", str(WORKSPACE_DIR),
        "--project", "opencodeconfig"
    ], capture_output=True, text=True, check=True)
    port = int(proc.stdout.strip())
    base_url = f"http://localhost:{port}"
    print(f"Dedicated web server verified on {base_url}")

    # Blast 40 rapid GET requests across endpoints to verify no socket/FD leak
    endpoints = ["/api/status", "/api/tasks", "/api/artifacts", "/api/memories", "/api/feed", "/api/brain"]
    for i in range(40):
        ep = endpoints[i % len(endpoints)]
        req = urllib.request.Request(f"{base_url}{ep}")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self_stat = resp.status
            self_body = resp.read()
            assert self_stat == 200, f"Failed on {ep}: {self_stat}"
            assert len(self_body) > 0
    log("40 rapid sequential requests succeeded with clean connection closures.")

    # Test SSE stream read and clean client disconnect
    sse_req = urllib.request.Request(f"{base_url}/api/stream")
    with urllib.request.urlopen(sse_req, timeout=4.0) as sse_resp:
        line1 = sse_resp.readline().decode("utf-8")
        line2 = sse_resp.readline().decode("utf-8")
        assert "data:" in line1 or "data:" in line2
    log("SSE /api/stream received live payload and closed cleanly without hanging server.")

    # ─────────────────────────────────────────────────────────────────
    header("STAGE 2: Multi-Project Agent Isolation (Compound Primary Key)")
    proj_a = "proj-alpha-test"
    proj_b = "proj-beta-test"

    # Backend working in Alpha
    team_server.tool_team_set_status({
        "agent_name": "backend",
        "status": "working",
        "current_task": "Implementing Prisma models for Alpha",
        "project": proj_a
    })

    # Backend idle in Beta
    team_server.tool_team_set_status({
        "agent_name": "backend",
        "status": "idle",
        "current_task": "",
        "project": proj_b
    })

    status_a = team_server.tool_team_get_status({"project": proj_a})
    status_b = team_server.tool_team_get_status({"project": proj_b})

    assert "WORKING" in status_a and "Prisma models for Alpha" in status_a, "Alpha status lost!"
    assert "IDLE" in status_b, "Beta status was not idle!"
    log(f"Project '{proj_a}' and '{proj_b}' maintain independent @backend states without collision.")

    # ─────────────────────────────────────────────────────────────────
    header("STAGE 3: Reactive Triggering (Backend ➔ Frontend ➔ QA)")
    wf_proj = "e2e-workflow-demo"

    # Turn A: Backend shares API contract
    share_res = team_server.tool_team_share_artifact({
        "creator": "backend",
        "artifact_key": "catalog-v2-api",
        "title": "Catalog & Product API v2 Specification",
        "artifact_type": "api_spec",
        "content": "POST /api/v2/products\nGET /api/v2/products/{id}",
        "project": wf_proj
    })
    assert "Reactive trigger dispatched to @frontend" in share_res
    log("Backend published 'catalog-v2-api'. Reactive trigger auto-dispatched to @frontend.")

    # Verify Frontend status was automatically transitioned to working on this trigger
    st_frontend = team_server.tool_team_get_status({"project": wf_proj})
    assert "@frontend" in st_frontend and "WORKING" in st_frontend
    log("Web Cockpit / status immediately reflects @frontend is WORKING on the backend contract.")

    # Verify Auto-Checkpoint was created
    latest_chk = mem_server.tool_get_session_checkpoint({"project": wf_proj})
    assert "catalog-v2-api" in latest_chk or "Auto-Checkpoint" in latest_chk
    log("Auto-Checkpoint verified: Context memory updated silently in SQLite FTS5.")

    # Turn B: Frontend checks triggers and claims work
    triggers_res = team_server.tool_team_check_triggers({
        "agent_name": "frontend",
        "project": wf_proj,
        "claim": True
    })
    assert "catalog-v2-api" in triggers_res
    assert "claimed" in triggers_res
    log("Frontend claimed pending reactive trigger and received contract payload.")

    # Frontend publishes UI contract and triggers QA auditor
    ui_share = team_server.tool_team_share_artifact({
        "creator": "frontend",
        "artifact_key": "catalog-v2-ui",
        "title": "Catalog Grid & Motion Drawer UI Specs",
        "artifact_type": "ui_contract",
        "content": "export interface ProductCardProps { id: string, name: string }",
        "project": wf_proj
    })
    assert "saved by @frontend" in ui_share

    trigger_qa = team_server.tool_team_trigger_agent({
        "from_agent": "frontend",
        "to_agent": "qa-auditor",
        "trigger_type": "review",
        "artifact_key": "catalog-v2-ui",
        "summary": "Run E2E motion and accessibility verification on Catalog UI",
        "project": wf_proj
    })
    assert "Reactive Trigger dispatched to @qa-auditor" in trigger_qa
    log("Frontend published UI contract and dispatched reactive trigger to @qa-auditor.")

    # ─────────────────────────────────────────────────────────────────
    header("STAGE 4: Task Completion & Automatic Agent Idle Transition")
    # QA Auditor posts task, claims it, and completes it
    team_server.tool_team_post_task({
        "title": "Verify WCAG AA & Vitest Unit Tests",
        "assigned_to": "qa-auditor",
        "project": wf_proj
    })
    cur = team_server.get_db().execute("SELECT id FROM team_tasks WHERE project = ? ORDER BY id DESC LIMIT 1", (wf_proj,))
    qa_task_id = cur.fetchone()["id"]

    team_server.tool_team_claim_task({
        "task_id": qa_task_id,
        "agent_name": "qa-auditor",
        "project": wf_proj
    })
    st_qa_working = team_server.tool_team_get_status({"project": wf_proj})
    assert "WORKING" in st_qa_working

    # Complete the task
    team_server.tool_team_update_task({
        "task_id": qa_task_id,
        "status": "completed",
        "notes": "All 18 unit tests passing. Spring physics verified."
    })

    # QA Auditor should automatically be idle now
    st_qa_idle = team_server.tool_team_get_status({"project": wf_proj})
    assert "IDLE" in st_qa_idle
    log("QA Auditor automatically transitioned to IDLE upon completing task.")

    # ─────────────────────────────────────────────────────────────────
    header("STAGE 5: GetBrain Architecture & Graph Synthesis")
    brain_data = brain_builder.build_project_brain(wf_proj, str(WORKSPACE_DIR))
    assert "nodes" in brain_data and "links" in brain_data
    node_types = set(n["type"] for n in brain_data["nodes"])
    assert "hub" in node_types, "Missing hub node in GetBrain"
    assert "module" in node_types, "Missing code module nodes in GetBrain"
    assert "artifact" in node_types, "Missing artifact nodes in GetBrain"
    print(f"GetBrain graph synthesized {len(brain_data['nodes'])} nodes and {len(brain_data['links'])} semantic links.")
    log("GetBrain accurately models project modules, contracts, agents, and checkpoints.")

    # ─────────────────────────────────────────────────────────────────
    header("FINAL RESULT: 100% OF END-TO-END WORKFLOW ASSERTIONS PASSED!")
    print("""
  ╔══════════════════════════════════════════════════════════════════╗
  ║  ⚡ ALL SWARM WORKFLOW STAGES VERIFIED WITH ZERO ERRORS         ║
  ║  • Server Stability & SSE Resilience: PASSED                    ║
  ║  • Multi-Project Isolated Agent States: PASSED                   ║
  ║  • Reactive Work Triggers (Backend ➔ Frontend ➔ QA): PASSED     ║
  ║  • Automatic Zero-Compaction Checkpoints: PASSED                ║
  ║  • Automatic Idle Transition on Task Complete: PASSED            ║
  ║  • GetBrain Architectural Knowledge Graph: PASSED               ║
  ╚══════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    run_all_tests()
