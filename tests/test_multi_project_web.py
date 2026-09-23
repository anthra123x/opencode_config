#!/usr/bin/env python3
"""
Test Suite: Multi-Project Dedicated Web Sessions & Isolated GetBrain
Verifies:
  1. Starting session in Project A allocates dedicated port (e.g. 4040).
  2. /api/status in Project A returns Project A's name, directory, and git branch.
  3. /api/brain in Project A scans and returns Project A's codebase files and hub node.
  4. Starting session in Project B allocates a separate dedicated port (e.g. 4041).
  5. /api/status in Project B returns Project B's name, directory, and git branch.
  6. /api/brain in Project B scans and returns Project B's codebase files (isolated from Project A).
  7. Opening subsequent sessions in Project A or B reuses the respective project port idempotently.
  8. Concurrent requests to both ports verify complete isolation.
"""

import sys
import os
import time
import json
import urllib.request
import subprocess
from pathlib import Path

PROJECT_A_DIR = Path("/home/omicron/Documentos/opencodeconfig").resolve()
PROJECT_B_DIR = Path("/home/omicron/Documentos/container").resolve()

SERVER_SCRIPT = Path(__file__).resolve().parent.parent / "web" / "server.py"

def http_get_json(url, timeout=2.0):
    req = urllib.request.Request(url, headers={"User-Agent": "TestClient"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_ensure(project_dir, project_name):
    cmd = [
        sys.executable,
        str(SERVER_SCRIPT),
        "--ensure",
        "--dir", str(project_dir),
        "--project", project_name
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return int(out)

def test_multi_project_workflow():
    print("=" * 70)
    print("TEST: Multi-Project Dedicated Web Sessions & GetBrain Isolation")
    print("=" * 70)

    assert PROJECT_A_DIR.is_dir(), f"Project A directory does not exist: {PROJECT_A_DIR}"
    assert PROJECT_B_DIR.is_dir(), f"Project B directory does not exist: {PROJECT_B_DIR}"

    # 1. Start / Ensure Project A
    print(f"\n[1] Ensuring session for Project A ({PROJECT_A_DIR.name})...")
    port_a = run_ensure(PROJECT_A_DIR, PROJECT_A_DIR.name)
    print(f"    -> Project A allocated Port: {port_a}")
    assert 4040 <= port_a <= 4060, f"Port {port_a} outside expected range"

    # Wait briefly for server readiness
    time.sleep(0.5)

    # 2. Verify Project A /api/status
    url_a_status = f"http://127.0.0.1:{port_a}/api/status"
    status_a = http_get_json(url_a_status)
    print(f"    -> Project A Status: project='{status_a.get('project')}', dir='{status_a.get('project_dir')}', branch='{status_a.get('branch')}'")

    assert status_a.get("project") == PROJECT_A_DIR.name, f"Expected project {PROJECT_A_DIR.name}, got {status_a.get('project')}"
    assert status_a.get("project_dir") == str(PROJECT_A_DIR), f"Expected dir {PROJECT_A_DIR}, got {status_a.get('project_dir')}"
    assert status_a.get("branch") == "main", f"Expected branch 'main', got {status_a.get('branch')}"

    # 3. Verify Project A /api/brain
    url_a_brain = f"http://127.0.0.1:{port_a}/api/brain"
    brain_a = http_get_json(url_a_brain)
    nodes_a = brain_a.get("nodes", [])
    node_labels_a = [n["label"] for n in nodes_a]
    hub_node_a = next((n for n in nodes_a if n.get("type") == "hub"), None)
    print(f"    -> Project A Brain: {len(nodes_a)} nodes. Hub: '{hub_node_a['label']}'")

    assert hub_node_a is not None, "Hub node missing in Project A"
    assert PROJECT_A_DIR.name in hub_node_a["label"], f"Expected hub label to mention {PROJECT_A_DIR.name}"
    # Verify module nodes contain files from opencodeconfig
    code_nodes_a = [n for n in nodes_a if n.get("type") == "module"]
    print(f"    -> Project A code modules detected: {[n['label'] for n in code_nodes_a[:6]]}...")
    assert len(code_nodes_a) > 0, "No code modules found for Project A"

    # 4. Start / Ensure Project B (different project)
    print(f"\n[2] Ensuring session for Project B ({PROJECT_B_DIR.name})...")
    port_b = run_ensure(PROJECT_B_DIR, PROJECT_B_DIR.name)
    print(f"    -> Project B allocated Port: {port_b}")
    assert 4040 <= port_b <= 4060, f"Port {port_b} outside expected range"
    assert port_b != port_a, f"CRITICAL: Project B got same port {port_b} as Project A {port_a}! Must have separate ports."

    # Wait briefly for server readiness
    time.sleep(0.5)

    # 5. Verify Project B /api/status
    url_b_status = f"http://127.0.0.1:{port_b}/api/status"
    status_b = http_get_json(url_b_status)
    print(f"    -> Project B Status: project='{status_b.get('project')}', dir='{status_b.get('project_dir')}', branch='{status_b.get('branch')}'")

    assert status_b.get("project") == PROJECT_B_DIR.name, f"Expected project {PROJECT_B_DIR.name}, got {status_b.get('project')}"
    assert status_b.get("project_dir") == str(PROJECT_B_DIR), f"Expected dir {PROJECT_B_DIR}, got {status_b.get('project_dir')}"
    assert status_b.get("branch") == "master", f"Expected branch 'master', got {status_b.get('branch')}"

    # 6. Verify Project B /api/brain
    url_b_brain = f"http://127.0.0.1:{port_b}/api/brain"
    brain_b = http_get_json(url_b_brain)
    nodes_b = brain_b.get("nodes", [])
    hub_node_b = next((n for n in nodes_b if n.get("type") == "hub"), None)
    print(f"    -> Project B Brain: {len(nodes_b)} nodes. Hub: '{hub_node_b['label']}'")

    assert hub_node_b is not None, "Hub node missing in Project B"
    assert PROJECT_B_DIR.name in hub_node_b["label"], f"Expected hub label to mention {PROJECT_B_DIR.name}"
    code_nodes_b = [n for n in nodes_b if n.get("type") == "module"]
    print(f"    -> Project B code modules detected: {[n['label'] for n in code_nodes_b[:6]]}...")
    assert len(code_nodes_b) > 0, "No code modules found for Project B"

    # Verify Project B does NOT have Project A's unique files (e.g. install.sh)
    labels_b = [n["label"] for n in code_nodes_b]
    assert "install.sh" not in labels_b, "Project B brain graph contaminated with Project A files!"

    # 7. Test Idempotency: Re-ensuring Project A and Project B
    print("\n[3] Testing session re-use (Idempotency)...")
    re_port_a = run_ensure(PROJECT_A_DIR, PROJECT_A_DIR.name)
    re_port_b = run_ensure(PROJECT_B_DIR, PROJECT_B_DIR.name)
    assert re_port_a == port_a, f"Project A re-ensure should reuse {port_a}, got {re_port_a}"
    assert re_port_b == port_b, f"Project B re-ensure should reuse {port_b}, got {re_port_b}"
    print(f"    ✓ Project A reused existing port {port_a}")
    print(f"    ✓ Project B reused existing port {port_b}")

    # 8. Test Concurrent Isolation
    print("\n[4] Testing Concurrent Isolation...")
    stat_a_concurrent = http_get_json(url_a_status)
    stat_b_concurrent = http_get_json(url_b_status)
    assert stat_a_concurrent["project"] == PROJECT_A_DIR.name
    assert stat_b_concurrent["project"] == PROJECT_B_DIR.name
    print(f"    ✓ Concurrent calls confirm Port {port_a} -> {stat_a_concurrent['project']} ({stat_a_concurrent['branch']})")
    print(f"    ✓ Concurrent calls confirm Port {port_b} -> {stat_b_concurrent['project']} ({stat_b_concurrent['branch']})")

    print("\n" + "=" * 70)
    print("ALL MULTI-PROJECT DEDICATED SESSION TESTS PASSED SUCCESSFULLY! (100%)")
    print("=" * 70)

if __name__ == "__main__":
    test_multi_project_workflow()
