#!/usr/bin/env python3
"""
Team Collaboration MCP Server (Team Swarm Bus)
Enables multi-agent communication, project-scoped shared task board, status sync,
handoffs, and artifact exchange between specialized sub-agents across sessions.
Standard JSON-RPC 2.0 stdio Model Context Protocol (MCP) server.
"""

import sys
import json
import os
import sqlite3
import datetime
import subprocess
from pathlib import Path

# Setup paths
DEFAULT_TEAM_DIR = Path.home() / ".opencode" / "team"
DB_PATH = Path(os.environ.get("OPENCODE_TEAM_DB", DEFAULT_TEAM_DIR / "team_collab.db"))

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
    return Path.cwd().name or "default"

def get_current_branch():
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except Exception:
        return ""

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    with conn:
        # Agent status registry with project tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_agents (
                agent_name TEXT PRIMARY KEY,
                project TEXT NOT NULL DEFAULT 'default',
                status TEXT NOT NULL DEFAULT 'idle',
                current_task TEXT DEFAULT '',
                blockers TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)
        # Feed / Messages with project scope
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL DEFAULT 'default',
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'status',
                priority TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL
            )
        """)
        # Shared Task Board with project scope
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                assigned_to TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'normal',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Shared Artifacts with project tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_artifacts (
                artifact_key TEXT PRIMARY KEY,
                project TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                creator TEXT NOT NULL,
                artifact_type TEXT NOT NULL DEFAULT 'general',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Migration helper for existing databases missing 'project' column
        for table in ["team_agents", "team_messages", "team_tasks", "team_artifacts"]:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN project TEXT NOT NULL DEFAULT 'default'")
            except sqlite3.OperationalError:
                pass

        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_team_artifacts_key_proj ON team_artifacts(artifact_key, project)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_team_agents_name_proj ON team_agents(agent_name, project)")
    return conn

# Tool Definitions
TOOLS = [
    {
        "name": "team_broadcast",
        "description": "Broadcast an update, handoff notification, or decision to the project's team bus so all sub-agents stay synchronized.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sender": {"type": "string", "description": "Agent name sending the message (e.g. 'orchestrator', 'backend', 'frontend', 'git-flow', 'qa-auditor', 'devops')"},
                "message": {"type": "string", "description": "Message content or progress summary"},
                "category": {"type": "string", "enum": ["status", "handoff", "question", "announcement", "warning"], "description": "Message classification"},
                "priority": {"type": "string", "enum": ["normal", "high", "urgent"], "description": "Priority level"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["sender", "message"]
        }
    },
    {
        "name": "team_read_feed",
        "description": "Read recent broadcast messages from teammates to catch up on what other agents completed in current or past sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of messages to retrieve (default 10)"},
                "category": {"type": "string", "description": "Optional category filter"},
                "since_id": {"type": "integer", "description": "Retrieve messages after this message ID"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            }
        }
    },
    {
        "name": "team_set_status",
        "description": "Update an agent's current working status, task, and any blockers on the project team board.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Agent name (e.g. 'orchestrator', 'backend', 'frontend', 'git-flow', 'qa-auditor', 'devops')"},
                "status": {"type": "string", "enum": ["idle", "working", "blocked", "ready_for_review"], "description": "Current agent status"},
                "current_task": {"type": "string", "description": "Brief description of the current task being executed"},
                "blockers": {"type": "string", "description": "Any blockers or dependencies (optional)"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["agent_name", "status"]
        }
    },
    {
        "name": "team_get_status",
        "description": "Retrieve a real-time snapshot of the development team for this project: active agents, tasks, artifacts, and cross-session progress.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            }
        }
    },
    {
        "name": "team_post_task",
        "description": "Post a task on the shared team board (used by Orchestrator or agents to delegate work across sessions).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short, actionable task title"},
                "description": {"type": "string", "description": "Detailed task instructions, acceptance criteria, or context"},
                "assigned_to": {"type": "string", "description": "Target agent (e.g. 'backend', 'frontend', 'git-flow', 'qa-auditor', 'devops')"},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "description": "Task priority"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "team_claim_task",
        "description": "Claim a task from the team board and mark it in_progress.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to claim"},
                "agent_name": {"type": "string", "description": "Agent claiming the task"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["task_id", "agent_name"]
        }
    },
    {
        "name": "team_update_task",
        "description": "Update the progress, status, or notes of a task on the team board.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "blocked", "review", "completed"], "description": "New task status"},
                "notes": {"type": "string", "description": "Progress notes, results, or links to shared artifacts"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["task_id", "status"]
        }
    },
    {
        "name": "team_list_tasks",
        "description": "List tasks from the shared team board with optional status or assignee filter.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (todo, in_progress, review, completed)"},
                "assigned_to": {"type": "string", "description": "Filter by assigned agent"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            }
        }
    },
    {
        "name": "team_share_artifact",
        "description": "Share a key contract or artifact (API spec, DB schema, UI component interface, test report) with other agents across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "creator": {"type": "string", "description": "Agent creating this artifact"},
                "artifact_key": {"type": "string", "description": "Unique key (e.g. 'auth-api-spec', 'user-table-schema', 'navbar-props')"},
                "title": {"type": "string", "description": "Descriptive title"},
                "artifact_type": {"type": "string", "enum": ["api_spec", "db_schema", "ui_contract", "pr_plan", "test_report", "general"], "description": "Artifact type"},
                "content": {"type": "string", "description": "Full artifact content, specification, or code contract"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["creator", "artifact_key", "title", "content"]
        }
    },
    {
        "name": "team_get_artifact",
        "description": "Retrieve a shared artifact by its key to consume contracts or specifications created by other agents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "artifact_key": {"type": "string", "description": "Unique key of the artifact"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["artifact_key"]
        }
    },
    {
        "name": "team_handoff",
        "description": "Directly hand off work from one specialist to another across turns or sessions, updating task state and posting a notification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_agent": {"type": "string", "description": "Agent releasing the task (e.g. 'backend')"},
                "to_agent": {"type": "string", "description": "Target agent receiving the handoff (e.g. 'frontend', 'git-flow', 'qa-auditor')"},
                "task_id": {"type": "integer", "description": "Optional task ID being handed off"},
                "notes": {"type": "string", "description": "Handoff context, instructions, or pointers to artifacts"},
                "artifact_key": {"type": "string", "description": "Optional artifact key containing contracts or deliverables"},
                "project": {"type": "string", "description": "Project scope (defaults to current project)"}
            },
            "required": ["from_agent", "to_agent", "notes"]
        }
    }
]

# Tool Implementations
def tool_team_broadcast(args):
    sender = args.get("sender", "").strip()
    message = args.get("message", "").strip()
    category = args.get("category", "status").strip().lower()
    priority = args.get("priority", "normal").strip().lower()
    project = get_current_project(args.get("project"))

    if not sender or not message:
        return "Error: sender and message must not be empty."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        conn.execute("""
            INSERT INTO team_messages (project, sender, message, category, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project, sender, message, category, priority, now))

    return f"✓ Broadcasted message from @{sender} [{project} | {category.upper()}]: '{message}'"

def tool_team_read_feed(args):
    limit = int(args.get("limit", 10))
    category = args.get("category", "")
    since_id = args.get("since_id")
    project = get_current_project(args.get("project"))

    conn = get_db()
    sql = "SELECT id, sender, message, category, priority, created_at FROM team_messages WHERE (project = ? OR project = 'default')"
    params = [project]
    if category:
        sql += " AND category = ?"
        params.append(category)
    if since_id is not None:
        sql += " AND id > ?"
        params.append(int(since_id))

    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cur = conn.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return f"No recent team messages found for project '{project}'."

    lines = [f"=== Team Activity Feed [{project}] ({len(rows)} message(s)) ==="]
    for r in reversed(rows):
        lines.append(f"#{r['id']} [@{r['sender']}] ({r['category'].upper()}) [{r['created_at']}]: {r['message']}")

    return "\n".join(lines)

def tool_team_set_status(args):
    agent_name = args.get("agent_name", "").strip()
    status = args.get("status", "idle").strip().lower()
    current_task = args.get("current_task", "").strip()
    blockers = args.get("blockers", "").strip()
    project = get_current_project(args.get("project"))

    if not agent_name:
        return "Error: agent_name must not be empty."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        conn.execute("""
            INSERT INTO team_agents (agent_name, project, status, current_task, blockers, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_name) DO UPDATE SET
                project = excluded.project,
                status = excluded.status,
                current_task = excluded.current_task,
                blockers = excluded.blockers,
                updated_at = excluded.updated_at
        """, (agent_name, project, status, current_task, blockers, now))

    return f"✓ Status updated for @{agent_name} [{project}]: {status.upper()} (Task: {current_task or 'none'})"

def tool_team_get_status(args):
    project = get_current_project(args.get("project"))
    branch = get_current_branch()
    branch_str = f" (branch: `{branch}`)" if branch else ""

    conn = get_db()

    # Query agents for this project
    cur_agents = conn.execute("""
        SELECT agent_name, status, current_task, blockers, updated_at
        FROM team_agents
        WHERE project = ? OR project = 'default'
        ORDER BY agent_name
    """, (project,))
    agents = cur_agents.fetchall()

    # Query tasks for this project
    cur_tasks = conn.execute("""
        SELECT id, title, assigned_to, status, priority, notes
        FROM team_tasks
        WHERE project = ?
        ORDER BY CASE status
            WHEN 'in_progress' THEN 1
            WHEN 'todo' THEN 2
            WHEN 'review' THEN 3
            WHEN 'blocked' THEN 4
            WHEN 'completed' THEN 5
            ELSE 6 END, id DESC
        LIMIT 20
    """, (project,))
    tasks = cur_tasks.fetchall()

    # Query shared artifacts
    cur_artifacts = conn.execute("""
        SELECT artifact_key, title, creator, artifact_type, updated_at
        FROM team_artifacts
        WHERE project = ?
        ORDER BY updated_at DESC LIMIT 10
    """, (project,))
    artifacts = cur_artifacts.fetchall()

    # Query latest 3 messages
    cur_feed = conn.execute("""
        SELECT sender, message, category, created_at
        FROM team_messages
        WHERE project = ?
        ORDER BY id DESC LIMIT 3
    """, (project,))
    feed = cur_feed.fetchall()

    out = [
        f"╔══════════════════════════════════════════════════════════════╗",
        f"║  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫  |  Project: {project:<15} ║",
        f"╚══════════════════════════════════════════════════════════════╝\n",
        f"**Project Workspace**: `{project}`{branch_str}\n"
    ]

    # Agents Roster
    out.append("### 👥 Sub-Agents Status")
    known_roles = {
        "orchestrator": ("#8B5CF6", "Lead Architect & Coordination"),
        "backend": ("#3B82F6", "APIs, Databases, Migrations & TDD"),
        "frontend": ("#EC4899", "UI/UX, Components & Micro-interactions"),
        "git-flow": ("#10B981", "Git/GitHub, Conventional Commits & PRs"),
        "qa-auditor": ("#F59E0B", "Verification Loop & Security Audits"),
        "devops": ("#06B6D4", "Docker, Containers & CI/CD Pipelines")
    }

    registered_agents = {a["agent_name"]: a for a in agents}
    for role, (color, desc) in known_roles.items():
        if role in registered_agents:
            a = registered_agents[role]
            icon = "🟢" if a["status"] == "working" else "🟡" if a["status"] == "ready_for_review" else "🔴" if a["status"] == "blocked" else "⚪"
            task = f" → `{a['current_task']}`" if a["current_task"] else ""
            blocker = f" [BLOCKER: {a['blockers']}]" if a["blockers"] else ""
            out.append(f"• {icon} **@{role}** ({a['status'].upper()}):{task}{blocker}")
        else:
            out.append(f"• ⚪ **@{role}** (IDLE): Ready for assignment")

    # Tasks Board
    out.append("\n### 📋 Project Task Board (Cross-Session)")
    if tasks:
        for t in tasks:
            assigned = f"[@{t['assigned_to']}]" if t['assigned_to'] else "[UNASSIGNED]"
            st = t['status'].upper()
            status_icon = "⏳" if t['status'] == 'in_progress' else "✅" if t['status'] == 'completed' else "📝" if t['status'] == 'todo' else "👀"
            out.append(f"• {status_icon} **#{t['id']}** {assigned} {t['title']} (`{st}`, Priority: {t['priority']})")
            if t['notes']:
                out.append(f"  └ Notes: {t['notes']}")
    else:
        out.append("• No tasks posted for this project yet. Use `team_post_task` to assign work.")

    # Shared Artifacts
    if artifacts:
        out.append("\n### 📦 Shared Project Artifacts & Contracts")
        for art in artifacts:
            out.append(f"• **`{art['artifact_key']}`** ({art['title']}) [{art['artifact_type'].upper()}] - by @{art['creator']}")

    # Latest Activity
    if feed:
        out.append("\n### 💬 Recent Team Announcements")
        for m in feed:
            out.append(f"• **@{m['sender']}** ({m['category']}): {m['message']}")

    return "\n".join(out)

def tool_team_post_task(args):
    title = args.get("title", "").strip()
    description = args.get("description", "").strip()
    assigned_to = args.get("assigned_to", "").strip()
    priority = args.get("priority", "normal").strip().lower()
    project = get_current_project(args.get("project"))

    if not title:
        return "Error: title must not be empty."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        cur = conn.execute("""
            INSERT INTO team_tasks (project, title, description, assigned_to, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'todo', ?, ?, ?)
        """, (project, title, description, assigned_to, priority, now, now))
        task_id = cur.lastrowid

    target = f"assigned to @{assigned_to}" if assigned_to else "unassigned"
    return f"✓ Task #{task_id} posted on [{project}] board: '{title}' ({target}, Priority: {priority})"

def tool_team_claim_task(args):
    task_id = int(args.get("task_id", 0))
    agent_name = args.get("agent_name", "").strip()
    project = get_current_project(args.get("project"))

    if not task_id or not agent_name:
        return "Error: task_id and agent_name are required."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        cur = conn.execute("""
            UPDATE team_tasks
            SET assigned_to = ?, status = 'in_progress', updated_at = ?
            WHERE id = ?
        """, (agent_name, now, task_id))
        if cur.rowcount == 0:
            return f"Task #{task_id} not found."

        cur_task = conn.execute("SELECT title FROM team_tasks WHERE id = ?", (task_id,)).fetchone()
        task_title = cur_task["title"] if cur_task else f"Task #{task_id}"

        conn.execute("""
            INSERT INTO team_agents (agent_name, project, status, current_task, updated_at)
            VALUES (?, ?, 'working', ?, ?)
            ON CONFLICT(agent_name) DO UPDATE SET
                project = excluded.project,
                status = 'working',
                current_task = excluded.current_task,
                updated_at = excluded.updated_at
        """, (agent_name, project, task_title, now))

    return f"✓ Task #{task_id} ('{task_title}') claimed by @{agent_name} in [{project}] and marked IN_PROGRESS."

def tool_team_update_task(args):
    task_id = int(args.get("task_id", 0))
    status = args.get("status", "in_progress").strip().lower()
    notes = args.get("notes", "").strip()

    if not task_id:
        return "Error: task_id is required."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        cur = conn.execute("""
            UPDATE team_tasks
            SET status = ?, notes = CASE WHEN ? != '' THEN ? ELSE notes END, updated_at = ?
            WHERE id = ?
        """, (status, notes, notes, now, task_id))
        if cur.rowcount == 0:
            return f"Task #{task_id} not found."

    return f"✓ Task #{task_id} updated to status '{status.upper()}'."

def tool_team_list_tasks(args):
    status = args.get("status", "")
    assigned_to = args.get("assigned_to", "")
    project = get_current_project(args.get("project"))

    conn = get_db()
    sql = "SELECT id, title, description, assigned_to, status, priority, notes, updated_at FROM team_tasks WHERE project = ?"
    params = [project]
    if status:
        sql += " AND status = ?"
        params.append(status)
    if assigned_to:
        sql += " AND assigned_to = ?"
        params.append(assigned_to)

    sql += " ORDER BY id DESC LIMIT 25"
    cur = conn.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return f"No tasks found for project '{project}' matching criteria."

    lines = [f"Shared Task Board for [{project}] ({len(rows)} item(s)):"]
    for r in rows:
        assignee = f"@{r['assigned_to']}" if r['assigned_to'] else "Unassigned"
        lines.append(f"• #{r['id']} [{r['status'].upper()}] {r['title']} ({assignee}, Priority: {r['priority']})")
        if r["notes"]:
            lines.append(f"  └ Notes: {r['notes']}")

    return "\n".join(lines)

def tool_team_share_artifact(args):
    creator = args.get("creator", "").strip()
    artifact_key = args.get("artifact_key", "").strip()
    title = args.get("title", "").strip()
    artifact_type = args.get("artifact_type", "general").strip()
    content = args.get("content", "").strip()
    project = get_current_project(args.get("project"))

    if not creator or not artifact_key or not title or not content:
        return "Error: creator, artifact_key, title, and content must all be provided."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        conn.execute("""
            INSERT INTO team_artifacts (artifact_key, project, title, creator, artifact_type, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_key) DO UPDATE SET
                project = excluded.project,
                title = excluded.title,
                creator = excluded.creator,
                artifact_type = excluded.artifact_type,
                content = excluded.content,
                updated_at = excluded.updated_at
        """, (artifact_key, project, title, creator, artifact_type, content, now, now))

    return f"✓ Artifact '{artifact_key}' ({title}) saved by @{creator} in [{project}]."

def tool_team_get_artifact(args):
    artifact_key = args.get("artifact_key", "").strip()
    project = get_current_project(args.get("project"))
    if not artifact_key:
        return "Error: artifact_key is required."

    conn = get_db()
    cur = conn.execute("""
        SELECT artifact_key, project, title, creator, artifact_type, content, updated_at
        FROM team_artifacts
        WHERE artifact_key = ? AND (project = ? OR project = 'default')
        ORDER BY (project = ?) DESC LIMIT 1
    """, (artifact_key, project, project))
    r = cur.fetchone()

    if not r:
        return f"Artifact '{artifact_key}' not found on [{project}] team board."

    return f"# [{r['artifact_type'].upper()}] {r['title']} (Key: {r['artifact_key']})\nProject: {r['project']} | Shared by: @{r['creator']} at {r['updated_at']}\n\n{r['content']}"

def tool_team_handoff(args):
    from_agent = args.get("from_agent", "").strip()
    to_agent = args.get("to_agent", "").strip()
    notes = args.get("notes", "").strip()
    task_id = args.get("task_id")
    artifact_key = args.get("artifact_key", "")
    project = get_current_project(args.get("project"))

    if not from_agent or not to_agent or not notes:
        return "Error: from_agent, to_agent, and notes are required."

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    with conn:
        # Update from_agent to ready_for_review / idle
        conn.execute("""
            INSERT INTO team_agents (agent_name, project, status, current_task, updated_at)
            VALUES (?, ?, 'idle', '', ?)
            ON CONFLICT(agent_name) DO UPDATE SET
                project = excluded.project,
                status = 'idle',
                current_task = '',
                updated_at = excluded.updated_at
        """, (from_agent, project, now))

        # Update to_agent to working
        current_task_desc = f"Handoff from @{from_agent}: {notes[:50]}"
        conn.execute("""
            INSERT INTO team_agents (agent_name, project, status, current_task, updated_at)
            VALUES (?, ?, 'working', ?, ?)
            ON CONFLICT(agent_name) DO UPDATE SET
                project = excluded.project,
                status = 'working',
                current_task = excluded.current_task,
                updated_at = excluded.updated_at
        """, (to_agent, project, current_task_desc, now))

        # If task_id provided, reassign or update task
        if task_id:
            conn.execute("""
                UPDATE team_tasks
                SET assigned_to = ?, status = 'in_progress', notes = ?, updated_at = ?
                WHERE id = ?
            """, (to_agent, f"Handed off from @{from_agent}: {notes}", now, int(task_id)))

        # Broadcast handoff announcement
        art_info = f" (Artifact: `{artifact_key}`)" if artifact_key else ""
        msg = f"🔄 HANDOFF: @{from_agent} handed off work to @{to_agent}.{art_info} Notes: {notes}"
        conn.execute("""
            INSERT INTO team_messages (project, sender, message, category, priority, created_at)
            VALUES (?, ?, ?, 'handoff', 'high', ?)
        """, (project, from_agent, msg, now))

    return f"✓ Handoff completed in [{project}]: @{from_agent} → @{to_agent}. {msg}"

TOOL_HANDLERS = {
    "team_broadcast": tool_team_broadcast,
    "team_read_feed": tool_team_read_feed,
    "team_set_status": tool_team_set_status,
    "team_get_status": tool_team_get_status,
    "team_post_task": tool_team_post_task,
    "team_claim_task": tool_team_claim_task,
    "team_update_task": tool_team_update_task,
    "team_list_tasks": tool_team_list_tasks,
    "team_share_artifact": tool_team_share_artifact,
    "team_get_artifact": tool_team_get_artifact,
    "team_handoff": tool_team_handoff,
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
                        "name": "team-collab-mcp",
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
