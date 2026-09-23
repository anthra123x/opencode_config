#!/usr/bin/env python3
"""
OpenCode Swarm Web Cockpit & GetBrain Local Server
Provides a real-time web dashboard and dynamic knowledge graph visualizer for OpenCode.
Features:
  - Per-project dedicated web sessions with dynamic port allocation (4040-4060)
  - Isolated GetBrain knowledge graph scanning the project's actual workspace
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
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import importlib.util

# Resolve server directories
SERVER_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = SERVER_DIR / "public"

# Dynamically locate and load team-collab MCP server module
possible_team_paths = [
    SERVER_DIR.parent / "mcp" / "team-collab" / "server.py",
    Path.home() / ".config" / "opencode" / "mcp" / "team-collab" / "server.py",
    Path("/home/omicron/Documentos/opencodeconfig/mcp/team-collab/server.py")
]
team_server_path = None
for p in possible_team_paths:
    if p.exists():
        team_server_path = p
        break

if not team_server_path:
    raise FileNotFoundError("Could not find team-collab MCP server script.")

team_spec = importlib.util.spec_from_file_location("team_collab_server", str(team_server_path))
team_server = importlib.util.module_from_spec(team_spec)
team_spec.loader.exec_module(team_server)

# Dynamically locate and load context-memory MCP server module
possible_mem_paths = [
    SERVER_DIR.parent / "mcp" / "context-memory" / "server.py",
    Path.home() / ".config" / "opencode" / "mcp" / "context-memory" / "server.py",
    Path("/home/omicron/Documentos/opencodeconfig/mcp/context-memory/server.py")
]
mem_server_path = None
for p in possible_mem_paths:
    if p.exists():
        mem_server_path = p
        break

mem_server = None
if mem_server_path:
    try:
        mem_spec = importlib.util.spec_from_file_location("context_memory_server", str(mem_server_path))
        mem_server = importlib.util.module_from_spec(mem_spec)
        mem_spec.loader.exec_module(mem_server)
    except Exception:
        pass

# Add web directory to path for brain_builder
sys.path.insert(0, str(SERVER_DIR))
import brain_builder

DEFAULT_PORT = 4040
PORT_RANGE_START = 4040
PORT_RANGE_END = 4060

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server to handle simultaneous SSE streams and REST calls per project."""
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, project_dir, project_name):
        super().__init__(server_address, RequestHandlerClass)
        self.project_dir = Path(project_dir).resolve()
        self.project_name = str(project_name)

    def get_branch(self):
        try:
            out = subprocess.check_output(
                ["git", "-C", str(self.project_dir), "branch", "--show-current"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            if out:
                return out
            out = subprocess.check_output(
                ["git", "-C", str(self.project_dir), "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            return out or "main"
        except Exception:
            return "main"

class SwarmWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def log_message(self, format, *args):
        try:
            msg = format % args
        except Exception:
            msg = str(format)
        # Suppress routine 200/SSE/favicon logs to keep terminal output clean
        if "/api/stream" in msg or " 200 -" in msg or "/favicon.ico" in msg or " 304 -" in msg:
            return
        sys.stderr.write(f"[OpenCode Swarm Web] {msg}\n")

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

        # Handle favicon quickly to prevent 404 logs
        if url == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        # 1. API: Swarm Status (Isolated per project)
        if url == "/api/status":
            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)
            branch = self.server.get_branch()
            conn = team_server.get_db()
            cur = conn.execute("""
                SELECT agent_name, status, current_task, blockers, window_id, last_heartbeat, updated_at
                FROM team_agents
                WHERE project = ? OR project = 'default'
                ORDER BY agent_name
            """, (proj,))
            agents = [dict(r) for r in cur.fetchall()]

            for a in agents:
                time_val = a["last_heartbeat"] or a["updated_at"]
                a["relative_time"] = team_server.format_relative_time(time_val)

            cur_tasks = conn.execute("SELECT COUNT(*) FROM team_tasks WHERE project = ? AND status = 'in_progress'", (proj,))
            in_prog_count = cur_tasks.fetchone()[0]

            self._send_json({
                "project": proj,
                "project_dir": proj_dir,
                "branch": branch,
                "agents": agents,
                "in_progress_tasks": in_prog_count,
                "clock": datetime.datetime.now().strftime("%H:%M:%S")
            })
            return

        # 2. API: Tasks Board (Isolated per project)
        if url == "/api/tasks":
            proj = self.server.project_name
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

        # 3. API: Artifacts & Contracts (Isolated per project)
        if url == "/api/artifacts":
            proj = self.server.project_name
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

        # 4. API: Context Memories (Isolated per project)
        if url == "/api/memories":
            proj = self.server.project_name
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

        # 5. API: Activity Feed (Isolated per project)
        if url == "/api/feed":
            proj = self.server.project_name
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

        # 6. API: GetBrain Knowledge Graph (Scans explicit project directory)
        if url == "/api/brain":
            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)
            brain_data = brain_builder.build_project_brain(proj, proj_dir)
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

            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)

            try:
                while True:
                    conn = team_server.get_db()
                    cur_ag = conn.execute("""
                        SELECT agent_name, status, current_task, blockers, window_id, last_heartbeat, updated_at
                        FROM team_agents
                        WHERE project = ? OR project = 'default'
                        ORDER BY agent_name
                    """, (proj,))
                    agents = [dict(r) for r in cur_ag.fetchall()]
                    for a in agents:
                        a["relative_time"] = team_server.format_relative_time(a["last_heartbeat"] or a["updated_at"])

                    cur_msg = conn.execute("""
                        SELECT id, sender, message, category, priority, created_at
                        FROM team_messages
                        WHERE project = ? OR project = 'default'
                        ORDER BY id DESC LIMIT 10
                    """, (proj,))
                    messages = [dict(r) for r in cur_msg.fetchall()]
                    for m in messages:
                        m["relative_time"] = team_server.format_relative_time(m["created_at"])

                    cur_tasks = conn.execute("""
                        SELECT id, title, description, assigned_to, status, priority, notes, updated_at
                        FROM team_tasks
                        WHERE project = ?
                        ORDER BY id DESC LIMIT 15
                    """, (proj,))
                    tasks = [dict(r) for r in cur_tasks.fetchall()]
                    for t in tasks:
                        t["relative_time"] = team_server.format_relative_time(t["updated_at"])

                    snapshot = {
                        "project": proj,
                        "project_dir": proj_dir,
                        "branch": self.server.get_branch(),
                        "clock": datetime.datetime.now().strftime("%H:%M:%S"),
                        "agents": agents,
                        "messages": messages,
                        "tasks": tasks
                    }
                    data_str = json.dumps(snapshot, ensure_ascii=False)

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
                "project": self.server.project_name
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
                "project": self.server.project_name
            })
            self._send_json({"success": True, "message": res})
            return

        if url == "/api/brain/scan":
            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)
            if mem_server:
                try:
                    mem_server.tool_auto_sync_project_memory({"project": proj, "workspace_dir": proj_dir})
                except Exception:
                    pass
            brain_data = brain_builder.build_project_brain(proj, proj_dir)
            self._send_json(brain_data)
            return

        if url == "/api/brain/checkpoint":
            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)
            summary = body.get("summary", "Checkpoint manual desde GetBrain Cockpit").strip()
            decisions = body.get("decisions", "").strip()
            next_steps = body.get("next_steps", "").strip()
            active_task = body.get("active_task", "").strip()
            files_mod = body.get("files_modified", "").strip()

            msg = "Checkpoint saved"
            if mem_server:
                try:
                    msg = mem_server.tool_checkpoint_session({
                        "project": proj,
                        "summary": summary,
                        "decisions": decisions,
                        "active_task": active_task,
                        "next_steps": next_steps,
                        "files_modified": files_mod
                    })
                except Exception as e:
                    msg = f"Error saving checkpoint: {e}"

            brain_data = brain_builder.build_project_brain(proj, proj_dir)
            self._send_json({"success": True, "message": msg, "brain": brain_data})
            return

        if url == "/api/brain/sync":
            proj = self.server.project_name
            proj_dir = str(self.server.project_dir)
            msg = "Context synced"
            if mem_server:
                try:
                    msg = mem_server.tool_auto_sync_project_memory({
                        "project": proj,
                        "workspace_dir": proj_dir
                    })
                except Exception as e:
                    msg = f"Error syncing: {e}"

            brain_data = brain_builder.build_project_brain(proj, proj_dir)
            self._send_json({"success": True, "message": msg, "brain": brain_data})
            return

        self._send_json({"error": "Not Found"}, status=404)

def check_server_status(port, timeout=0.35):
    """Probes http://127.0.0.1:<port>/api/status and returns its dict payload or None."""
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}/api/status"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenCode-Discovery"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data
    except Exception:
        pass
    return None

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex(('127.0.0.1', port)) == 0

def resolve_project_info(given_dir=None, given_project=None):
    if given_dir:
        pdir = Path(given_dir).resolve()
    else:
        try:
            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            if root and os.path.isdir(root):
                pdir = Path(root).resolve()
            else:
                pdir = Path.cwd().resolve()
        except Exception:
            pdir = Path.cwd().resolve()

    if given_project and str(given_project).strip():
        pname = str(given_project).strip()
    else:
        pname = pdir.name or "default"

    return pdir, pname

def find_or_assign_port(project_dir, project_name, start_port=PORT_RANGE_START, max_port=PORT_RANGE_END):
    """
    Scans port range to find an existing server for this project.
    If none exists, returns the first available free port.
    Returns (port, is_already_running).
    """
    pdir_str = str(Path(project_dir).resolve())
    first_free = None

    for port in range(start_port, max_port + 1):
        if is_port_in_use(port):
            status = check_server_status(port)
            if status:
                s_dir = status.get("project_dir", "")
                s_proj = status.get("project", "")
                if s_dir == pdir_str or (s_proj and s_proj == project_name):
                    return port, True
        else:
            if first_free is None:
                first_free = port

    if first_free is not None:
        return first_free, False

    # Fallback to ephemeral port
    import socket
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1], False

def ensure_server(project_dir, project_name, open_browser=False):
    """
    Ensures a dedicated server for this project is running in the background.
    Prints the assigned port number and exits.
    """
    port, running = find_or_assign_port(project_dir, project_name)
    url = f"http://localhost:{port}"

    if running:
        if open_browser:
            webbrowser.open(url)
        print(port)
        return port

    # Launch daemon server on assigned port
    script_path = str(Path(__file__).resolve())
    cmd = [
        sys.executable,
        script_path,
        "--dir", str(project_dir),
        "--project", project_name,
        "--port", str(port)
    ]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    # Wait up to 1.5s for port to start listening
    for _ in range(15):
        time.sleep(0.1)
        if is_port_in_use(port):
            break

    if open_browser:
        webbrowser.open(url)

    print(port)
    return port

def start_server(project_dir, project_name, port=0, open_browser=False):
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # Auto-assign port if not specified
    if port == 0:
        port, is_running = find_or_assign_port(project_dir, project_name)
        if is_running:
            url = f"http://localhost:{port}"
            if open_browser:
                print(f"OpenCode Swarm Web server already active on {url} for project '{project_name}'. Opening browser...")
                webbrowser.open(url)
            else:
                print(f"OpenCode Swarm Web server is already running on {url} for project '{project_name}'.")
            return
    else:
        # Check if specified port is in use
        if is_port_in_use(port):
            status = check_server_status(port)
            if status:
                s_dir = status.get("project_dir", "")
                s_proj = status.get("project", "")
                pdir_str = str(Path(project_dir).resolve())
                if s_dir == pdir_str or s_proj == project_name:
                    url = f"http://localhost:{port}"
                    if open_browser:
                        print(f"OpenCode Swarm Web server already active on {url} for project '{project_name}'. Opening browser...")
                        webbrowser.open(url)
                    else:
                        print(f"OpenCode Swarm Web server is already running on {url} for project '{project_name}'.")
                    return
                else:
                    # Port belongs to another project; re-allocate
                    print(f"Port {port} is occupied by project '{s_proj}'. Allocating dedicated port...")
                    port, is_running = find_or_assign_port(project_dir, project_name)
                    if is_running:
                        url = f"http://localhost:{port}"
                        if open_browser:
                            webbrowser.open(url)
                        return

    try:
        httpd = ThreadedHTTPServer(("127.0.0.1", port), SwarmWebHandler, project_dir, project_name)
    except OSError as err:
        print(f"Cannot bind to port {port}: {err}")
        return

    url = f"http://localhost:{port}"

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫  |  Web Cockpit & GetBrain   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  → Project:   {project_name}")
    print(f"  → Directory: {project_dir}")
    print(f"  → Branch:    {httpd.get_branch()}")
    print(f"  → Dashboard: \033[1;36m{url}\033[0m")
    print(f"  → GetBrain:  \033[1;35m{url}/#brain\033[0m")
    print(f"  → Status:    Live SSE Stream Connected (Dedicated Session)")
    print("────────────────────────────────────────────────────────────────")
    print("  Press Ctrl+C to stop the web server.\n")

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\nStopping OpenCode Swarm Web server for '{project_name}'...")
        httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCode Swarm Web Cockpit & GetBrain Server")
    parser.add_argument("--dir", type=str, default="", help="Project root directory path (defaults to git root or CWD)")
    parser.add_argument("--project", type=str, default="", help="Project name (defaults to directory name)")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on (default 0 for auto-assign per project 4040-4060)")
    parser.add_argument("--ensure", action="store_true", help="Ensure dedicated server is running in background and print port")
    parser.add_argument("--open", action="store_true", help="Automatically open the web dashboard in your browser")
    args = parser.parse_args()

    pdir, pname = resolve_project_info(args.dir, args.project)

    if args.ensure:
        ensure_server(pdir, pname, open_browser=args.open)
    else:
        start_server(pdir, pname, port=args.port, open_browser=args.open)
