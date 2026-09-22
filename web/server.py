#!/usr/bin/env python3
"""
OpenCode Swarm Web Cockpit & GetBrain Local Server
Provides a real-time web dashboard and dynamic knowledge graph visualizer for OpenCode.
Features:
  - Zero external dependencies (pure Python 3 standard library)
  - REST API for swarm status, tasks, artifacts, memories, and brain graph
  - Server-Sent Events (SSE) for instant, live browser reactivity across terminal sessions
  - Multi-threaded HTTP server
"""

import sys
import os
import json
import time
import argparse
import webbrowser
import threading
import sqlite3
import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

import importlib.util

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load team-collab MCP server directly from path to avoid circular import with web/server.py
team_spec = importlib.util.spec_from_file_location("team_collab_server", str(REPO_ROOT / "mcp" / "team-collab" / "server.py"))
team_server = importlib.util.module_from_spec(team_spec)
team_spec.loader.exec_module(team_server)

sys.path.insert(0, str(REPO_ROOT / "web"))
import brain_builder

DEFAULT_PORT = 4040
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server to handle simultaneous SSE streams and REST calls."""
    daemon_threads = True

class SwarmWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress routine 200/SSE logs to keep terminal output clean
        if "/api/stream" in args[0] or "200 -" in args[0]:
            return
        sys.stderr.write(f"[OpenCode Swarm Web] {args[0]}\n")

    def _send_json(self, data, status=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def do_GET(self):
        url = self.path.split("?")[0]

        # 1. API: Swarm Status
        if url == "/api/status":
            proj = team_server.get_current_project()
            conn = team_server.get_db()
            cur = conn.execute("""
                SELECT agent_name, status, current_task, blockers, window_id, last_heartbeat, updated_at
                FROM team_agents
                WHERE project = ? OR project = 'default'
                ORDER BY agent_name
            """, (proj,))
            agents = [dict(r) for r in cur.fetchall()]

            # Format relative time
            for a in agents:
                time_val = a["last_heartbeat"] or a["updated_at"]
                a["relative_time"] = team_server.format_relative_time(time_val)

            cur_tasks = conn.execute("SELECT COUNT(*) FROM team_tasks WHERE project = ? AND status = 'in_progress'", (proj,))
            in_prog_count = cur_tasks.fetchone()[0]

            self._send_json({
                "project": proj,
                "branch": team_server.get_current_branch(),
                "agents": agents,
                "in_progress_tasks": in_prog_count,
                "clock": datetime.datetime.now().strftime("%H:%M:%S")
            })
            return

        # 2. API: Tasks Board
        if url == "/api/tasks":
            proj = team_server.get_current_project()
            conn = team_server.get_db()
            cur = conn.execute("""
                SELECT id, title, description, assigned_to, status, priority, notes, updated_at
                FROM team_tasks
                WHERE project = ?
                ORDER BY id DESC
            """, (proj,))
            tasks = [dict(r) for r in cur.fetchall()]
            for t in tasks:
                t["relative_time"] = team_server.format_relative_time(t["updated_at"])

            self._send_json({
                "project": proj,
                "tasks": tasks
            })
            return

        # 3. API: Artifacts & Contracts
        if url == "/api/artifacts":
            proj = team_server.get_current_project()
            conn = team_server.get_db()
            cur = conn.execute("""
                SELECT artifact_key, title, creator, artifact_type, content, updated_at
                FROM team_artifacts
                WHERE project = ? OR project = 'default'
                ORDER BY updated_at DESC
            """, (proj,))
            artifacts = [dict(r) for r in cur.fetchall()]
            for art in artifacts:
                art["relative_time"] = team_server.format_relative_time(art["updated_at"])

            self._send_json({
                "project": proj,
                "artifacts": artifacts
            })
            return

        # 4. API: Context Memories
        if url == "/api/memories":
            proj = team_server.get_current_project()
            mem_db_path = Path(os.environ.get("OPENCODE_MEMORY_DB", brain_builder.DEFAULT_MEM_DIR / "context_memory.db"))
            conn = brain_builder.get_db_connection(mem_db_path)
            memories = []
            if conn:
                cur = conn.execute("""
                    SELECT id, key, category, content, tags, project, updated_at
                    FROM memories
                    WHERE project = ? OR project = 'global'
                    ORDER BY updated_at DESC
                """, (proj,))
                memories = [dict(r) for r in cur.fetchall()]
                conn.close()

            self._send_json({
                "project": proj,
                "memories": memories
            })
            return

        # 5. API: Activity Feed
        if url == "/api/feed":
            proj = team_server.get_current_project()
            conn = team_server.get_db()
            cur = conn.execute("""
                SELECT id, sender, message, category, priority, created_at
                FROM team_messages
                WHERE project = ? OR project = 'default'
                ORDER BY id DESC LIMIT 25
            """, (proj,))
            feed = [dict(r) for r in cur.fetchall()]
            for m in feed:
                m["relative_time"] = team_server.format_relative_time(m["created_at"])

            self._send_json({
                "project": proj,
                "feed": feed
            })
            return

        # 6. API: GetBrain Knowledge Graph
        if url == "/api/brain":
            proj = team_server.get_current_project()
            workspace = os.getcwd()
            brain_data = brain_builder.build_project_brain(proj, workspace)
            self._send_json(brain_data)
            return

        # 7. Real-Time Server-Sent Events (SSE) Stream
        if url == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            proj = team_server.get_current_project()
            last_check = ""

            try:
                while True:
                    # Collect current snapshot
                    conn = team_server.get_db()
                    cur_ag = conn.execute("SELECT agent_name, status, current_task, blockers, window_id, last_heartbeat, updated_at FROM team_agents WHERE project = ? OR project = 'default' ORDER BY agent_name", (proj,))
                    agents = [dict(r) for r in cur_ag.fetchall()]
                    for a in agents:
                        a["relative_time"] = team_server.format_relative_time(a["last_heartbeat"] or a["updated_at"])

                    cur_msg = conn.execute("SELECT id, sender, message, category, priority, created_at FROM team_messages WHERE project = ? OR project = 'default' ORDER BY id DESC LIMIT 10", (proj,))
                    messages = [dict(r) for r in cur_msg.fetchall()]
                    for m in messages:
                        m["relative_time"] = team_server.format_relative_time(m["created_at"])

                    cur_tasks = conn.execute("SELECT id, title, description, assigned_to, status, priority, notes, updated_at FROM team_tasks WHERE project = ? ORDER BY id DESC LIMIT 15", (proj,))
                    tasks = [dict(r) for r in cur_tasks.fetchall()]
                    for t in tasks:
                        t["relative_time"] = team_server.format_relative_time(t["updated_at"])

                    snapshot = {
                        "project": proj,
                        "branch": team_server.get_current_branch(),
                        "clock": datetime.datetime.now().strftime("%H:%M:%S"),
                        "agents": agents,
                        "messages": messages,
                        "tasks": tasks
                    }
                    data_str = json.dumps(snapshot, ensure_ascii=False)

                    # Send event
                    self.wfile.write(f"data: {data_str}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                return
            return

        # Serve static assets from public/ directory
        return super().do_GET()

    def do_POST(self):
        url = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            body = json.loads(post_data)
        except Exception:
            body = {}

        if url == "/api/task/create":
            title = body.get("title", "").strip()
            if not title:
                self._send_json({"error": "Task title required"}, status=400)
                return
            res = team_server.tool_team_post_task({
                "title": title,
                "description": body.get("description", ""),
                "assigned_to": body.get("assigned_to", ""),
                "priority": body.get("priority", "normal"),
                "project": team_server.get_current_project()
            })
            self._send_json({"success": True, "message": res})
            return

        if url == "/api/broadcast":
            msg = body.get("message", "").strip()
            sender = body.get("sender", "orchestrator").strip()
            if not msg:
                self._send_json({"error": "Message required"}, status=400)
                return
            res = team_server.tool_team_broadcast({
                "sender": sender,
                "message": msg,
                "category": body.get("category", "announcement"),
                "priority": body.get("priority", "normal"),
                "project": team_server.get_current_project()
            })
            self._send_json({"success": True, "message": res})
            return

        if url == "/api/brain/scan":
            proj = team_server.get_current_project()
            brain_data = brain_builder.build_project_brain(proj, os.getcwd())
            self._send_json(brain_data)
            return

        self._send_json({"error": "Not Found"}, status=404)

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_server(port=DEFAULT_PORT, open_browser=False):
    # Ensure public dir exists
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # If server is already running on port, avoid starting a duplicate process
    if is_port_in_use(port):
        url = f"http://localhost:{port}"
        if open_browser:
            print(f"OpenCode Swarm Web server already active on {url}. Opening browser...")
            webbrowser.open(url)
            return
        else:
            print(f"OpenCode Swarm Web server is already running on {url}")
            return

    try:
        httpd = ThreadedHTTPServer(("127.0.0.1", port), SwarmWebHandler)
    except OSError as err:
        print(f"Cannot bind to port {port}: {err}")
        return

    url = f"http://localhost:{port}"
    project = team_server.get_current_project()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫  |  Web Cockpit & GetBrain   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  → Project:   {project}")
    print(f"  → Dashboard: \033[1;36m{url}\033[0m")
    print(f"  → GetBrain:  \033[1;35m{url}/#brain\033[0m")
    print(f"  → Status:    Live SSE Stream Connected")
    print("────────────────────────────────────────────────────────────────")
    print("  Press Ctrl+C to stop the web server.\n")

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping OpenCode Swarm Web server...")
        httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCode Swarm Web Cockpit & GetBrain Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default 4040)")
    parser.add_argument("--open", action="store_true", help="Automatically open the web dashboard in your browser")
    args = parser.parse_args()

    start_server(port=args.port, open_browser=args.open)
