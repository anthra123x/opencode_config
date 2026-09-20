#!/usr/bin/env python3
"""
Interactive Simulation Runner for OpenCode Swarm Session
Simulates an end-to-end multi-agent software engineering session testing:
- Branding and Swarm HUD
- Persistent context memory (SQLite FTS5)
- Team Swarm Bus (team-collab MCP)
- Every specialized sub-agent and skill:
  * @orchestrator (council, architecture breakdown)
  * @backend (postgres-patterns, prisma-patterns, tdd-workflow, error-handling)
  * @frontend (impeccable, design-taste-frontend, emil-design-eng)
  * @qa-auditor (verification-loop, production-audit, ai-regression-testing)
  * @git-flow (git-flow-pro, conventional commits)
"""

import os
import sys
import time
from pathlib import Path

# Add MCP servers with distinct module names
import importlib.util
REPO_DIR = Path(__file__).resolve().parent.parent

def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

memory_mcp = load_module("memory_mcp", REPO_DIR / "mcp" / "context-memory" / "server.py")
team_mcp   = load_module("team_mcp", REPO_DIR / "mcp" / "team-collab" / "server.py")

PROJECT = "ecommerce-core"

# ANSI Styling
C_PURPLE = "\033[38;5;141m"
C_CYAN   = "\033[38;5;51m"
C_BLUE   = "\033[38;5;39m"
C_PINK   = "\033[38;5;205m"
C_GREEN  = "\033[38;5;48m"
C_AMBER  = "\033[38;5;214m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_RESET  = "\033[0m"

def section(title):
    print(f"\n{C_PURPLE}{C_BOLD}{'━' * 66}{C_RESET}")
    print(f"{C_PURPLE}{C_BOLD}  {title}{C_RESET}")
    print(f"{C_PURPLE}{C_BOLD}{'━' * 66}{C_RESET}\n")

def agent_say(role, color, text):
    print(f"{color}{C_BOLD}[@{role}]{C_RESET} {text}")

def main():
    print(f"{C_PURPLE}{C_BOLD}╔══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_PURPLE}{C_BOLD}║       ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫ — SESSION SIMULATION     ║{C_RESET}")
    print(f"{C_PURPLE}{C_BOLD}║       Project: {PROJECT:<24} Branch: feature/catalog-v1 ║{C_RESET}")
    print(f"{C_PURPLE}{C_BOLD}╚══════════════════════════════════════════════════════════════╝{C_RESET}")

    # ──────────────── TURN 1: Bootstrap & Context Hydration ────────────────
    section("TURN 1: Session Initiation & Persistent Memory Hydration")
    agent_say("orchestrator", C_PURPLE, "Bootstrapping session from persistent context memory...")

    # Remember project foundation if not present
    memory_mcp.tool_sync_project_context({
        "project": PROJECT,
        "tech_stack": "Next.js 15, PostgreSQL 16, Prisma ORM, Tailwind CSS v4, Motion",
        "architecture_notes": "Modular domain-driven structure, strict Zod validation, HTTP-only JWT cookies",
        "conventions": "Conventional Commits 1.0, 80% test coverage threshold, WCAG AA compliance"
    })

    bootstrap_info = memory_mcp.tool_get_session_bootstrap({"project": PROJECT})
    print(f"{C_DIM}{bootstrap_info}{C_RESET}\n")

    agent_say("orchestrator", C_PURPLE,
        "Welcome to Session 1 in 'ecommerce-core'! We are ready to build the Product Catalog & Cart.\n"
        "Breaking down user objective into domain-specific tasks on the Swarm board..."
    )

    # ──────────────── TURN 2: Task Planning & Board Setup ────────────────
    section("TURN 2: Swarm Task Board Initialization")
    t1 = team_mcp.tool_team_post_task({
        "title": "Build Product Catalog REST & Database Schema",
        "description": "PostgreSQL schema with Prisma, index on category_id and price, endpoints GET /api/v1/products and POST /api/v1/cart",
        "assigned_to": "backend",
        "priority": "high",
        "project": PROJECT
    })
    print(f"  {t1}")

    t2 = team_mcp.tool_team_post_task({
        "title": "Design Animated Product Grid & Cart Drawer UI",
        "description": "Responsive grid with OKLCH theme, spring physics for cart drawer, and accessibility ARIA states",
        "assigned_to": "frontend",
        "priority": "high",
        "project": PROJECT
    })
    print(f"  {t2}")

    t3 = team_mcp.tool_team_post_task({
        "title": "Run Verification Loop & Security Audit",
        "description": "Build, typecheck, lint, unit tests (>=80% coverage), SQL injection checks, AI regression tests",
        "assigned_to": "qa-auditor",
        "priority": "normal",
        "project": PROJECT
    })
    print(f"  {t3}")

    t4 = team_mcp.tool_team_post_task({
        "title": "Prepare Conventional Commits & Pull Request",
        "description": "Review diffs, ensure no secrets/console logs, format feat(catalog) commit, craft PR description",
        "assigned_to": "git-flow",
        "priority": "normal",
        "project": PROJECT
    })
    print(f"  {t4}")

    # ──────────────── TURN 3: @backend Execution ────────────────
    section("TURN 3: @backend — Database Patterns, TDD & API Contracts")
    agent_say("backend", C_BLUE, "Claiming Task #1. Applying 'postgres-patterns' & 'prisma-patterns'...")

    claim_b = team_mcp.tool_team_claim_task({"task_id": 1, "agent_name": "backend", "project": PROJECT})
    print(f"  {claim_b}")

    agent_say("backend", C_BLUE,
        "Executing 'tdd-workflow':\n"
        "  1. RED: tests/api/products.test.ts created (failing).\n"
        "  2. GREEN: prisma/schema.prisma updated with Product & CartItem models. Index on [categoryId, price].\n"
        "  3. REFACTOR: src/controllers/products.ts with typed error handling & Zod schemas.\n"
        "  4. Test suite: 6 tests passing, 88.4% coverage."
    )

    # Share contract
    api_spec = """
openapi: 3.1.0
paths:
  /api/v1/products:
    get:
      summary: List paginated products
      parameters:
        - name: categoryId
          in: query
          schema: { type: string }
        - name: page
          in: query
          schema: { type: integer, default: 1 }
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        id: { type: string }
                        title: { type: string }
                        priceCents: { type: integer }
                        imageUrl: { type: string }
                        stock: { type: integer }
  /api/v1/cart:
    post:
      summary: Add item to cart
      requestBody:
        content:
          application/json:
            schema:
              properties:
                productId: { type: string }
                quantity: { type: integer }
    """
    share_res = team_mcp.tool_team_share_artifact({
        "creator": "backend",
        "artifact_key": "catalog-api-v1",
        "title": "Product Catalog API Specification",
        "artifact_type": "api_spec",
        "content": api_spec,
        "project": PROJECT
    })
    print(f"  {share_res}")

    # Handoff to frontend
    handoff_res = team_mcp.tool_team_handoff({
        "from_agent": "backend",
        "to_agent": "frontend",
        "task_id": 1,
        "notes": "Backend API complete. Contracts available at 'catalog-api-v1'. Ready for UI consumption.",
        "artifact_key": "catalog-api-v1",
        "project": PROJECT
    })
    print(f"  {handoff_res}")

    # ──────────────── TURN 4: @frontend Execution ────────────────
    section("TURN 4: @frontend — Impeccable Design, Motion & Component Crafting")
    agent_say("frontend", C_PINK, "Consuming backend artifact 'catalog-api-v1' via MCP...")

    contract = team_mcp.tool_team_get_artifact({"artifact_key": "catalog-api-v1", "project": PROJECT})
    print(f"  {C_DIM}Retrieved {len(contract)} bytes from artifact 'catalog-api-v1'{C_RESET}")

    agent_say("frontend", C_PINK,
        "Applying 'design-taste-frontend' (Variance: High, Motion: Tactile Spring, Density: Balanced):\n"
        "  • Implemented ProductCard component using OKLCH neutral palette & vibrant accent tags.\n"
        "  • Animated Cart Drawer using 'emil-design-eng' spring physics (stiffness: 320, damping: 28).\n"
        "  • Added WCAG AA compliant aria-live regions for cart item counter.\n"
        "  • Zero UI slop, clean focus-visible rings and smooth skeleton loading states."
    )

    team_mcp.tool_team_update_task({"task_id": 2, "status": "completed", "notes": "Product grid and animated cart drawer completed.", "project": PROJECT})
    team_mcp.tool_team_broadcast({
        "sender": "frontend",
        "message": "Frontend components built, styled, and connected to API contract.",
        "category": "handoff",
        "priority": "high",
        "project": PROJECT
    })

    # ──────────────── TURN 5: @qa-auditor Execution ────────────────
    section("TURN 5: @qa-auditor — Verification Loop & Security Audit")
    agent_say("qa-auditor", C_AMBER, "Initiating 6-stage 'verification-loop'...")

    print(
        f"  {C_GREEN}✓ Stage 1 (Build):{C_RESET}     npm run build succeeded in 2.1s (zero warnings)\n"
        f"  {C_GREEN}✓ Stage 2 (Types):{C_RESET}     tsc --noEmit passed (100% strict type safety)\n"
        f"  {C_GREEN}✓ Stage 3 (Lint):{C_RESET}      biome check . passed (zero formatting/lint errors)\n"
        f"  {C_GREEN}✓ Stage 4 (Tests):{C_RESET}     14/14 unit & integration tests passed (89.2% coverage)\n"
        f"  {C_GREEN}✓ Stage 5 (Security):{C_RESET}  Audit clean — SQL injection safe, JWT verified\n"
        f"  {C_GREEN}✓ Stage 6 (Regress):{C_RESET}   'ai-regression-testing' verified edge cases & null safety"
    )

    team_mcp.tool_team_share_artifact({
        "creator": "qa-auditor",
        "artifact_key": "qa-signoff-catalog",
        "title": "QA Verification Sign-off Report",
        "artifact_type": "test_report",
        "content": "All 6 stages passed. Build green, 89.2% test coverage, security clean. Production ready.",
        "project": PROJECT
    })
    team_mcp.tool_team_update_task({"task_id": 3, "status": "completed", "notes": "Full verification loop passed (89.2% coverage).", "project": PROJECT})

    # ──────────────── TURN 6: @git-flow Execution ────────────────
    section("TURN 6: @git-flow — Git Flow Pro & Conventional Commits")
    agent_say("git-flow", C_GREEN, "Reviewing working tree diffs and crafting Conventional Commit...")

    print(
        f"  {C_DIM}git status: 8 files modified, zero untracked temp files{C_RESET}\n"
        f"  {C_DIM}git diff check: No secrets, no console.log statements detected{C_RESET}\n"
        f"  {C_BOLD}Commit Message Crafted:{C_RESET}\n"
        f"    feat(catalog): add product catalog api and animated cart drawer\n\n"
        f"    - Implement PostgreSQL Product & CartItem models with Prisma\n"
        f"    - Add paginated GET /api/v1/products and POST /api/v1/cart endpoints\n"
        f"    - Build animated ProductGrid and CartDrawer with spring physics\n"
        f"    - Unit test coverage at 89.2% verified by QA\n"
    )

    team_mcp.tool_team_update_task({"task_id": 4, "status": "completed", "notes": "Commit created and PR plan ready.", "project": PROJECT})

    # ──────────────── TURN 7: @orchestrator Synthesis ────────────────
    section("TURN 7: Swarm Delivery & Persistent Memory Retention")
    memory_mcp.tool_remember({
        "key": f"{PROJECT}-catalog-architecture",
        "content": "Product catalog uses paginated GET with category index; Cart drawer uses spring physics; Auth via signed cookies.",
        "category": "architecture",
        "tags": "catalog, cart, architecture",
        "project": PROJECT
    })

    status_dashboard = team_mcp.tool_team_get_status({"project": PROJECT})
    print(status_dashboard)

    print(f"\n{C_PURPLE}{C_BOLD}✨ SIMULATION COMPLETED SUCCESSFULLY! All sub-agents, MCPs, and skills verified.{C_RESET}\n")

if __name__ == "__main__":
    main()
