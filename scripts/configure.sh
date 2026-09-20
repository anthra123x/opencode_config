#!/usr/bin/env bash
set -euo pipefail

# configure.sh — Re-runnable configuration wizard
# Called by: ecc configure
# Can also run standalone: ./scripts/configure.sh

CONFIG_DIR="${ECC_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}"
SKILLS_DIR="${ECC_SKILLS:-$HOME/.opencode/skills}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"
if [ ! -f "$LIB_DIR/ui.sh" ] && [ -f "$CONFIG_DIR/lib/ui.sh" ]; then
  LIB_DIR="$CONFIG_DIR/lib"
fi

source "$LIB_DIR/ui.sh"
source "$LIB_DIR/paths.sh"
source "$LIB_DIR/utils.sh"

setup_ui
setup_paths
setup_utils

print_banner
msgbox "Configuration Wizard" \
"This wizard lets you reconfigure your OpenCode Swarm setup.

You can change preferences, paths, and re-generate configuration files.
Existing files will be backed up automatically."

# ─── User info ───
USER_NAME=$(inputbox "User" "Your name or alias:" "${USER:-user}")
GITHUB_HANDLE=$(inputbox "GitHub" "GitHub username (optional):" "")

# ─── Config paths ───
CONFIG_PATH=$(inputbox "Config path" "Config directory:" "$CONFIG_DIR")
SKILLS_PATH=$(inputbox "Skills path" "Skills directory:" "$SKILLS_DIR")

# ─── Generate opencode.jsonc ───
if yesno "Generate config" "Regenerate opencode.jsonc with Swarm settings?"; then
  cat > "$CONFIG_PATH/opencode.jsonc" <<EOF
{
  "\$schema": "https://opencode.ai/config.json",
  "default_agent": "orchestrator",
  "instructions": [
    "INSTRUCTIONS.md",
    "AGENTS.md"
  ],
  "skills": {
    "paths": [
      "$SKILLS_PATH"
    ]
  },
  "agent": {
    "orchestrator": {
      "mode": "primary",
      "color": "#8B5CF6",
      "description": "Team Lead & Orchestrator. Analyzes user requirements, plans architecture, delegates tasks to specialists (@backend, @frontend, @git-flow, @qa-auditor), and synthesizes deliverables."
    },
    "backend": {
      "mode": "subagent",
      "color": "#3B82F6",
      "description": "Specialized Backend Engineer. Builds robust APIs, database schemas and migrations (PostgreSQL, Prisma, MySQL, JPA), business logic, and backend unit tests."
    },
    "frontend": {
      "mode": "subagent",
      "color": "#EC4899",
      "description": "Specialized Frontend & UI/UX Engineer. Builds modern responsive web interfaces with curated typography, micro-animations, accessible components, and anti-slop design."
    },
    "git-flow": {
      "mode": "subagent",
      "color": "#10B981",
      "description": "Specialized Git and GitHub Workflow Manager. Manages branch lifecycles, conventional semantic commits, PR reviews and summaries, merge conflict resolution, and release hygiene."
    },
    "qa-auditor": {
      "mode": "subagent",
      "color": "#F59E0B",
      "description": "Specialized Quality Assurance & Verification Auditor. Audits test suites, ensures coverage >=80%, conducts security and production-readiness checks, and detects AI regressions."
    },
    "devops": {
      "mode": "subagent",
      "color": "#06B6D4",
      "description": "Specialized DevOps and Infrastructure Engineer. Crafts lean multi-stage Dockerfiles, Docker Compose setups, non-root configurations, and CI/CD pipelines."
    }
  },
  "permission": {
    "skill": {
      "*": "allow"
    }
  },
  "compaction": {
    "auto": true,
    "tail_turns": 30
  }
}
EOF
  log "Regenerated opencode.jsonc"
fi

# ─── Summary ───
echo ""
echo -e "${C_GREEN}${C_BOLD}Configuration updated successfully:${C_NC}"
echo "  User:    $USER_NAME $([[ -n "$GITHUB_HANDLE" ]] && echo "($GITHUB_HANDLE)")"
echo "  Config:  $CONFIG_PATH"
echo "  Skills:  $SKILLS_PATH"
echo ""
echo -e "Run ${C_BOLD}ecc doctor${C_NC} to verify everything is working."
