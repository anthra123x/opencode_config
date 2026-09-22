#!/usr/bin/env python3
"""
Context Memory MCP Server
Provides persistent cross-session memory with SQLite FTS5 full-text search,
project auto-scoping, and instant session bootstrapping.
Standard JSON-RPC 2.0 stdio Model Context Protocol (MCP) server.
"""

import sys
import json
import os
import sqlite3
import datetime
import subprocess
import time
import random
from pathlib import Path
from contextlib import contextmanager

# Paths & Setup
DEFAULT_DB_DIR = Path.home() / ".opencode" / "memory"
DB_PATH = Path(os.environ.get("OPENCODE_MEMORY_DB", DEFAULT_DB_DIR / "context_memory.db"))

@contextmanager
def db_write_lock(conn, max_retries=10, base_delay=0.03):
    for attempt in range(max_retries):
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
                return
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if ("locked" in err_msg or "busy" in err_msg) and attempt < max_retries - 1:
                sleep_time = (base_delay * (1.6 ** attempt)) + random.uniform(0.01, 0.04)
                time.sleep(sleep_time)
                continue
            raise

def get_current_project(explicit=None):
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        if root:
            return Path(root).name
    except Exception:
        pass
    return Path.cwd().name or "global"

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                project TEXT DEFAULT 'global',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Create FTS table if not exists
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    key, category, content, tags, project, content=memories, content_rowid=id
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, key, category, content, tags, project)
                    VALUES (new.id, new.key, new.category, new.content, new.tags, new.project);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, key, category, content, tags, project)
                    VALUES ('delete', old.id, old.key, old.category, old.content, old.tags, old.project);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, key, category, content, tags, project)
                    VALUES ('delete', old.id, old.key, old.category, old.content, old.tags, old.project);
                    INSERT INTO memories_fts(rowid, key, category, content, tags, project)
                    VALUES (new.id, new.key, new.category, new.content, new.tags, new.project);
                END;
            """)
        except sqlite3.OperationalError:
            pass
    return conn

# Tool Definitions
TOOLS = [
    {
        "name": "remember",
        "description": "Store or update a persistent memory item (architectural decision, user preference, API pattern, bugfix note, convention) linked to the project or global scope.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Unique identifier or concise title for the memory (e.g. 'auth-jwt-spec', 'user-prefers-typescript')"},
                "content": {"type": "string", "description": "Detailed memory content, decision rationale, or specification."},
                "category": {"type": "string", "enum": ["architecture", "preference", "decision", "convention", "snippet", "bugfix", "general"], "description": "Category classification"},
                "tags": {"type": "string", "description": "Comma-separated tags (e.g. 'auth, security, jwt')"},
                "project": {"type": "string", "description": "Project identifier (defaults to current project or 'global')"}
            },
            "required": ["key", "content"]
        }
    },
    {
        "name": "recall",
        "description": "Search and retrieve stored memories using full-text keyword search and optional filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query or keywords to look for"},
                "category": {"type": "string", "description": "Filter by category (optional)"},
                "project": {"type": "string", "description": "Filter by project name (defaults to current project + global)"},
                "limit": {"type": "integer", "description": "Maximum number of results to return (default 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_memories",
        "description": "List existing stored memories with metadata for browsing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (optional)"},
                "project": {"type": "string", "description": "Filter by project name (defaults to current project + global)"},
                "limit": {"type": "integer", "description": "Maximum items to return (default 20)"}
            }
        }
    },
    {
        "name": "delete_memory",
        "description": "Delete a stored memory item by key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key of the memory to delete"}
            },
            "required": ["key"]
        }
    },
    {
        "name": "get_active_context",
        "description": "Retrieve an executive summary of all active architectural decisions, preferences, and project guidelines to bootstrap agent context across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project identifier (defaults to current project)"}
            }
        }
    },
    {
        "name": "get_session_bootstrap",
        "description": "Instant cross-session hydration. Returns persistent memories, tech stack, and active task board status for the current project to orient the swarm at turn 1.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project identifier (defaults to current project)"}
            }
        }
    },
    {
        "name": "sync_project_context",
        "description": "Convenience tool to register or update the core context of the current project (tech stack, architecture notes, conventions).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name or path (defaults to current project)"},
                "tech_stack": {"type": "string", "description": "Technologies, frameworks, databases used"},
                "architecture_notes": {"type": "string", "description": "Key architectural constraints and decisions"},
                "conventions": {"type": "string", "description": "Code and workflow conventions"}
            }
        }
    }
]

# Tool Implementations
def tool_remember(args):
    key = args.get("key", "").strip()
    content = args.get("content", "").strip()
    category = args.get("category", "general").strip().lower()
    tags = args.get("tags", "").strip()
    project = get_current_project(args.get("project"))

    if not key or not content:
        return "Error: key and content must be non-empty."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with db_write_lock(conn):
        conn.execute("""
            INSERT INTO memories (key, category, content, tags, project, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                category = excluded.category,
                content = excluded.content,
                tags = excluded.tags,
                project = excluded.project,
                updated_at = excluded.updated_at
        """, (key, category, content, tags, project, now, now))

    return f"✓ Memory saved: '{key}' [Category: {category}, Project: {project}]"

def tool_recall(args):
    query = args.get("query", "").strip()
    category = args.get("category", "")
    project = get_current_project(args.get("project"))
    limit = int(args.get("limit", 5))

    if not query:
        return "Error: query must not be empty."

    conn = get_db()
    results = []

    try:
        clean_q = '"' + query.replace('"', '""') + '"'
        sql = """
            SELECT m.key, m.category, m.content, m.tags, m.project, m.updated_at
            FROM memories_fts f
            JOIN memories m ON m.id = f.rowid
            WHERE memories_fts MATCH ?
        """
        params = [clean_q]
        if category:
            sql += " AND m.category = ?"
            params.append(category)
        if project:
            sql += " AND (m.project = ? OR m.project = 'global')"
            params.append(project)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        cur = conn.execute(sql, params)
        results = [dict(row) for row in cur.fetchall()]
    except Exception:
        sql = """
            SELECT key, category, content, tags, project, updated_at
            FROM memories
            WHERE (key LIKE ? OR content LIKE ? OR tags LIKE ?)
        """
        like_p = f"%{query}%"
        params = [like_p, like_p, like_p]
        if category:
            sql += " AND category = ?"
            params.append(category)
        if project:
            sql += " AND (project = ? OR project = 'global')"
            params.append(project)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(sql, params)
        results = [dict(row) for row in cur.fetchall()]

    if not results:
        return f"No memories found matching '{query}' for [{project}]."

    output = [f"Found {len(results)} memory match(es) for [{project}]:"]
    for r in results:
        output.append(f"\n--- [{r['category'].upper()}] {r['key']} (Scope: {r['project']}) ---")
        if r.get("tags"):
            output.append(f"Tags: {r['tags']}")
        output.append(f"Content: {r['content']}")
        output.append(f"Updated: {r['updated_at']}")

    return "\n".join(output)

def tool_list_memories(args):
    category = args.get("category", "")
    project = get_current_project(args.get("project"))
    limit = int(args.get("limit", 20))

    conn = get_db()
    sql = "SELECT key, category, content, tags, project, updated_at FROM memories WHERE (project = ? OR project = 'global')"
    params = [project]
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    cur = conn.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return f"No memories stored yet for project '{project}'."

    lines = [f"Stored memories for [{project}] ({len(rows)} item(s)):"]
    for r in rows:
        snippet = r['content'].replace('\n', ' ')
        if len(snippet) > 80:
            snippet = snippet[:77] + "..."
        lines.append(f"• [{r['category']}] {r['key']} ({r['project']}): {snippet}")

    return "\n".join(lines)

def tool_delete_memory(args):
    key = args.get("key", "").strip()
    if not key:
        return "Error: key must not be empty."

    conn = get_db()
    with db_write_lock(conn):
        cur = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        if cur.rowcount > 0:
            return f"✓ Memory '{key}' removed successfully."
        else:
            return f"Memory '{key}' not found."

def tool_get_active_context(args):
    project = get_current_project(args.get("project"))
    conn = get_db()
    cur = conn.execute("""
        SELECT category, key, content, tags, project
        FROM memories
        WHERE project = ? OR project = 'global'
        ORDER BY (project = ?) DESC, category, updated_at DESC
        LIMIT 30
    """, (project, project))
    rows = cur.fetchall()

    if not rows:
        return f"No context memories found for project '{project}' or global scope."

    sections = {}
    for r in rows:
        cat = r["category"].upper()
        if cat not in sections:
            sections[cat] = []
        scope = f"[{r['project']}] " if r['project'] != project else ""
        sections[cat].append(f"• **{r['key']}**: {scope}{r['content']}")

    output = [f"# Active Context Memories for [{project}]"]
    for cat, items in sections.items():
        output.append(f"\n## {cat}")
        output.extend(items)

    return "\n".join(output)

def tool_get_session_bootstrap(args):
    project = get_current_project(args.get("project"))
    context = tool_get_active_context({"project": project})

    # Try to fetch team status from team database
    team_db_path = Path(os.environ.get("OPENCODE_TEAM_DB", Path.home() / ".opencode" / "team" / "team_collab.db"))
    team_summary = []
    if team_db_path.exists():
        try:
            conn = sqlite3.connect(str(team_db_path))
            conn.row_factory = sqlite3.Row
            # Active tasks
            cur = conn.execute("SELECT id, title, assigned_to, status, priority FROM team_tasks WHERE project = ? ORDER BY id DESC LIMIT 5", (project,))
            tasks = cur.fetchall()
            if tasks:
                team_summary.append("### Active Tasks from Previous Session(s):")
                for t in tasks:
                    team_summary.append(f"• #{t['id']} [{t['status'].upper()}] @{t['assigned_to'] or 'unassigned'}: {t['title']}")

            # Recent handoff / broadcast
            cur_msg = conn.execute("SELECT sender, message FROM team_messages WHERE project = ? ORDER BY id DESC LIMIT 2", (project,))
            msgs = cur_msg.fetchall()
            if msgs:
                team_summary.append("\n### Recent Handoffs:")
                for m in msgs:
                    team_summary.append(f"• @{m['sender']}: {m['message']}")
        except Exception:
            pass

    out = [
        f"╔══════════════════════════════════════════════════════════════╗",
        f"║  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫  |  Project: {project:<15} ║",
        f"╚══════════════════════════════════════════════════════════════╝\n",
        context,
        "\n## 👥 Team Board Status",
        "\n".join(team_summary) if team_summary else "• Ready for initial task breakdown and assignment."
    ]
    return "\n".join(out)

def tool_sync_project_context(args):
    project = get_current_project(args.get("project"))
    results = []

    if "tech_stack" in args and args["tech_stack"]:
        tool_remember({
            "key": f"{project}-tech-stack",
            "content": args["tech_stack"],
            "category": "architecture",
            "project": project,
            "tags": "stack, technology, setup"
        })
        results.append("tech stack")

    if "architecture_notes" in args and args["architecture_notes"]:
        tool_remember({
            "key": f"{project}-architecture",
            "content": args["architecture_notes"],
            "category": "architecture",
            "project": project,
            "tags": "architecture, design, patterns"
        })
        results.append("architecture")

    if "conventions" in args and args["conventions"]:
        tool_remember({
            "key": f"{project}-conventions",
            "content": args["conventions"],
            "category": "convention",
            "project": project,
            "tags": "rules, conventions, guidelines"
        })
        results.append("conventions")

    return f"✓ Synchronized project context for [{project}]: updated {', '.join(results) if results else 'ready'}."

TOOL_HANDLERS = {
    "remember": tool_remember,
    "recall": tool_recall,
    "list_memories": tool_list_memories,
    "delete_memory": tool_delete_memory,
    "get_active_context": tool_get_active_context,
    "get_session_bootstrap": tool_get_session_bootstrap,
    "sync_project_context": tool_sync_project_context,
}

# MCP JSON-RPC Stdio Loop
def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception as e:
            sys.stderr.write(f"Invalid JSON: {e}\n")
            continue

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "context-memory-mcp",
                        "version": "2.0.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": TOOLS
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            handler = TOOL_HANDLERS.get(tool_name)
            if handler:
                try:
                    text_output = handler(tool_args)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": text_output
                                }
                            ]
                        }
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32603,
                            "message": f"Execution error in {tool_name}: {str(e)}"
                        }
                    }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        else:
            if msg_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not supported: {method}"
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    main()
