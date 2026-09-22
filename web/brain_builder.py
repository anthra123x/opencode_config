#!/usr/bin/env python3
"""
GetBrain Knowledge Graph Synthesizer
Generates an interactive, living project knowledge graph connecting:
  - Sub-Agents (Specialists in active/idle states)
  - Tasks (In-progress, review, completed, todo)
  - Contracts & Artifacts (API specs, DB schemas, UI interfaces)
  - Context Memories (Architectural decisions, rules, conventions)
  - Codebase Modules (Key files and architecture components in the workspace)
"""

import os
import sqlite3
import datetime
from pathlib import Path

# Paths
DEFAULT_TEAM_DIR = Path.home() / ".opencode" / "team"
DEFAULT_MEM_DIR = Path.home() / ".opencode" / "memory"

AGENT_METADATA = {
    "orchestrator": {"color": "#8B5CF6", "glyph": "👑", "title": "Lead Architect"},
    "backend":      {"color": "#3B82F6", "glyph": "⚡", "title": "Backend Specialist"},
    "frontend":     {"color": "#EC4899", "glyph": "🎨", "title": "Frontend Specialist"},
    "git-flow":     {"color": "#10B981", "glyph": "🌿", "title": "Git Flow Manager"},
    "qa-auditor":   {"color": "#F59E0B", "glyph": "🛡️", "title": "QA & Security Auditor"},
    "devops":       {"color": "#06B6D4", "glyph": "🐳", "title": "DevOps & Containers"}
}

def get_db_connection(db_path):
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn
    except Exception:
        return None

def scan_project_modules(project_dir, max_files=25):
    """
    Scans the workspace to identify key architectural files and modules
    to anchor in the GetBrain knowledge graph.
    """
    modules = []
    p = Path(project_dir)
    if not p.is_dir():
        return modules

    ignore_dirs = {
        "node_modules", ".git", ".next", ".cache", "dist", "build",
        "__pycache__", ".venv", "venv", ".idea", ".vscode", "coverage"
    }
    valid_exts = {".ts", ".tsx", ".js", ".jsx", ".py", ".sql", ".prisma", ".json", ".md"}

    count = 0
    try:
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            rel_dir = os.path.relpath(root, p)
            if rel_dir.count(os.sep) > 3:
                continue

            for f in files:
                if count >= max_files:
                    break
                ext = Path(f).suffix.lower()
                if ext in valid_exts and not f.startswith("."):
                    rel_path = os.path.join(rel_dir, f) if rel_dir != "." else f
                    # Categorize module
                    cat = "general"
                    low = rel_path.lower()
                    if "component" in low or "ui" in low or "view" in low:
                        cat = "ui_component"
                    elif "api" in low or "route" in low or "controller" in low or "service" in low:
                        cat = "api_route"
                    elif "model" in low or "schema" in low or "db" in low or "migration" in low:
                        cat = "db_model"
                    elif "test" in low or "spec" in low:
                        cat = "test_suite"
                    elif "config" in low or "instruction" in low or "agent" in low:
                        cat = "config_rule"

                    modules.append({
                        "path": rel_path,
                        "name": f,
                        "category": cat,
                        "size": os.path.getsize(os.path.join(root, f))
                    })
                    count += 1
    except Exception:
        pass

    return modules

def build_project_brain(project_name="default", workspace_dir=None):
    """
    Synthesizes the dynamic GetBrain Knowledge Graph for the current project.
    Returns:
      {
        "project": project_name,
        "nodes": [...],
        "links": [...],
        "stats": {...}
      }
    """
    team_db_path = Path(os.environ.get("OPENCODE_TEAM_DB", DEFAULT_TEAM_DIR / "team_collab.db"))
    mem_db_path = Path(os.environ.get("OPENCODE_MEMORY_DB", DEFAULT_MEM_DIR / "context_memory.db"))

    nodes = []
    links = []
    node_ids = set()

    def add_node(node_id, node_type, label, category, color, details=None, status="active", extra=None):
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        node_obj = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "category": category,
            "color": color,
            "status": status,
            "details": details or "",
            "extra": extra or {}
        }
        nodes.append(node_obj)

    def add_link(source_id, target_id, label, link_type="general", animated=False):
        if source_id not in node_ids or target_id not in node_ids:
            return
        links.append({
            "source": source_id,
            "target": target_id,
            "label": label,
            "type": link_type,
            "animated": animated
        })

    # 1. Add Project Hub Node
    hub_id = f"project:{project_name}"
    add_node(
        node_id=hub_id,
        node_type="hub",
        label=f"Project: {project_name}",
        category="core",
        color="#7C3AED",
        details=f"Central coordination nexus for project '{project_name}'."
    )

    # 2. Add Specialized Agent Nodes
    conn_team = get_db_connection(team_db_path)
    agents_map = {}
    if conn_team:
        try:
            cur = conn_team.execute("""
                SELECT agent_name, status, current_task, blockers, window_id, last_heartbeat, updated_at
                FROM team_agents
                WHERE project = ? OR project = 'default'
            """, (project_name,))
            for row in cur.fetchall():
                agents_map[row["agent_name"]] = dict(row)
        except Exception:
            pass

    for agent_key, meta in AGENT_METADATA.items():
        ag_data = agents_map.get(agent_key, {})
        status = ag_data.get("status", "idle")
        curr_task = ag_data.get("current_task", "")
        win_id = ag_data.get("window_id", "")
        last_hb = ag_data.get("last_heartbeat", ag_data.get("updated_at", ""))

        node_id = f"agent:{agent_key}"
        label = f"@{agent_key}"
        add_node(
            node_id=node_id,
            node_type="agent",
            label=label,
            category=agent_key,
            color=meta["color"],
            status=status,
            details=f"**{meta['title']}**\n- Status: `{status.upper()}`\n- Task: `{curr_task or 'idle'}`\n- Window: `{win_id or 'none'}`",
            extra={
                "glyph": meta["glyph"],
                "window_id": win_id,
                "current_task": curr_task,
                "last_heartbeat": last_hb,
                "role_title": meta["title"]
            }
        )
        add_link(hub_id, node_id, "participates_in", link_type="member")

    # 3. Add Shared Artifacts & Contracts
    artifacts = []
    if conn_team:
        try:
            cur = conn_team.execute("""
                SELECT artifact_key, title, creator, artifact_type, content, updated_at
                FROM team_artifacts
                WHERE project = ? OR project = 'default'
                ORDER BY updated_at DESC LIMIT 15
            """, (project_name,))
            artifacts = [dict(r) for r in cur.fetchall()]
        except Exception:
            pass

    for art in artifacts:
        art_id = f"artifact:{art['artifact_key']}"
        art_color = "#10B981" if "api" in art["artifact_type"] else "#EC4899" if "ui" in art["artifact_type"] else "#3B82F6"
        add_node(
            node_id=art_id,
            node_type="artifact",
            label=art["title"] or art["artifact_key"],
            category=art["artifact_type"],
            color=art_color,
            details=art["content"][:600] + ("..." if len(art["content"]) > 600 else ""),
            extra={
                "artifact_key": art["artifact_key"],
                "creator": art["creator"],
                "artifact_type": art["artifact_type"],
                "full_content": art["content"],
                "updated_at": art["updated_at"]
            }
        )
        # Link Creator -> Artifact
        creator_id = f"agent:{art['creator']}"
        if creator_id in node_ids:
            add_link(creator_id, art_id, "published_contract", link_type="contract", animated=True)
        else:
            add_link(hub_id, art_id, "contract_of", link_type="contract")

        # Auto-link consumers: If backend created api_spec, link to frontend
        if art["artifact_type"] == "api_spec" and "agent:frontend" in node_ids:
            add_link(art_id, "agent:frontend", "consumed_by", link_type="dependency", animated=True)
        # If frontend created ui_contract, link to qa-auditor
        if art["artifact_type"] in ("ui_contract", "design_token") and "agent:qa-auditor" in node_ids:
            add_link(art_id, "agent:qa-auditor", "verified_by", link_type="dependency")

    # 4. Add Tasks from Task Board
    tasks = []
    if conn_team:
        try:
            cur = conn_team.execute("""
                SELECT id, title, description, assigned_to, status, priority, notes, updated_at
                FROM team_tasks
                WHERE project = ?
                ORDER BY id DESC LIMIT 20
            """, (project_name,))
            tasks = [dict(r) for r in cur.fetchall()]
        except Exception:
            pass

    for t in tasks:
        task_id = f"task:{t['id']}"
        t_color = "#F59E0B" if t["status"] == "in_progress" else "#10B981" if t["status"] == "completed" else "#6B7280"
        add_node(
            node_id=task_id,
            node_type="task",
            label=f"#{t['id']} {t['title'][:30]}",
            category=t["status"],
            color=t_color,
            status=t["status"],
            details=f"**Task #{t['id']}**: {t['title']}\n- Status: `{t['status'].upper()}`\n- Assignee: `@{t['assigned_to'] or 'none'}`\n- Priority: `{t['priority']}`\n\n{t['description']}\n\n*Notes*: {t['notes']}",
            extra=t
        )
        # Link to Assignee
        if t["assigned_to"]:
            assignee_id = f"agent:{t['assigned_to']}"
            if assignee_id in node_ids:
                is_anim = (t["status"] == "in_progress")
                add_link(assignee_id, task_id, "assigned_to", link_type="work", animated=is_anim)
            else:
                add_link(hub_id, task_id, "task_of", link_type="task")
        else:
            add_link(hub_id, task_id, "unassigned_task", link_type="task")

    # 5. Add Persistent Context Memories
    conn_mem = get_db_connection(mem_db_path)
    memories = []
    if conn_mem:
        try:
            cur = conn_mem.execute("""
                SELECT id, key, category, content, tags, project, updated_at
                FROM memories
                WHERE project = ? OR project = 'global'
                ORDER BY updated_at DESC LIMIT 15
            """, (project_name,))
            memories = [dict(r) for r in cur.fetchall()]
        except Exception:
            pass

    for m in memories:
        mem_id = f"memory:{m['key']}"
        m_color = "#8B5CF6" if m["category"] == "architecture" else "#F43F5E" if m["category"] == "decision" else "#EAB308"
        add_node(
            node_id=mem_id,
            node_type="memory",
            label=f"🧠 {m['key']}",
            category=m["category"],
            color=m_color,
            details=f"**[{m['category'].upper()}] {m['key']}** (Scope: {m['project']})\n\n{m['content']}\n\n*Tags*: `{m.get('tags', '')}`",
            extra=m
        )
        # Connect memory to hub or orchestrator
        if "agent:orchestrator" in node_ids and m["category"] in ("architecture", "decision"):
            add_link("agent:orchestrator", mem_id, "anchored_decision", link_type="memory")
        else:
            add_link(hub_id, mem_id, "rule_of", link_type="memory")

    # 6. Add Codebase Module Nodes (if workspace provided)
    if workspace_dir:
        code_modules = scan_project_modules(workspace_dir, max_files=20)
        for mod in code_modules:
            mod_id = f"code:{mod['path']}"
            mod_color = "#38BDF8" if mod["category"] == "ui_component" else "#A855F7" if mod["category"] == "api_route" else "#34D399"
            add_node(
                node_id=mod_id,
                node_type="module",
                label=mod["name"],
                category=mod["category"],
                color=mod_color,
                details=f"**File Module**: `{mod['path']}`\n- Type: `{mod['category']}`\n- Size: `{mod['size']} bytes`",
                extra=mod
            )
            # Link to corresponding specialist agent
            if mod["category"] == "ui_component" and "agent:frontend" in node_ids:
                add_link("agent:frontend", mod_id, "crafts_component", link_type="code")
            elif mod["category"] in ("api_route", "db_model") and "agent:backend" in node_ids:
                add_link("agent:backend", mod_id, "implements_logic", link_type="code")
            elif mod["category"] == "test_suite" and "agent:qa-auditor" in node_ids:
                add_link("agent:qa-auditor", mod_id, "tests_code", link_type="code")
            else:
                add_link(hub_id, mod_id, "contains_file", link_type="code")

    # Close connections
    if conn_team:
        try: conn_team.close()
        except: pass
    if conn_mem:
        try: conn_mem.close()
        except: pass

    # Stats
    stats = {
        "total_nodes": len(nodes),
        "total_links": len(links),
        "agents_count": len([n for n in nodes if n["type"] == "agent"]),
        "tasks_count": len([n for n in nodes if n["type"] == "task"]),
        "artifacts_count": len([n for n in nodes if n["type"] == "artifact"]),
        "memories_count": len([n for n in nodes if n["type"] == "memory"]),
        "modules_count": len([n for n in nodes if n["type"] == "module"]),
        "generated_at": datetime.datetime.now().isoformat()
    }

    return {
        "project": project_name,
        "nodes": nodes,
        "links": links,
        "stats": stats
    }

if __name__ == "__main__":
    import json
    data = build_project_brain("opencodeconfig", os.getcwd())
    print(f"Synthesized GetBrain: {data['stats']['total_nodes']} nodes, {data['stats']['total_links']} links.")
    print(json.dumps(data["stats"], indent=2))
