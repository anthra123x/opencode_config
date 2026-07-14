#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO_DIR/lib/ui.sh"
source "$REPO_DIR/lib/paths.sh"
source "$REPO_DIR/lib/utils.sh"

setup_ui
setup_paths
setup_utils

# ──────────────── STEP: Welcome ────────────────

print_banner
msgbox "Welcome" \
"Welcome to the opencode Configuration Manager!

This installer will set up:

  • 33 ECC skills for engineering, testing, DB, design, infra
  • Engineering methodology (INSTRUCTIONS.md)
  • Knowledge graph agent rules (AGENTS.md)
  • MCP server integration

Two modes available:
  - Quickstart: minimal prompts, best for AI-assisted setup
  - Manual: full control over every option

Total install size: ~500KB  |  Time: 30-90 seconds"

# ──────────────── STEP: Prerequisites ────────────────

PREREQ_FAIL=false
infobox "Checking" "Checking prerequisites..."

# Check bash version >= 4
if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
  warn "bash 4+ required (found ${BASH_VERSINFO[0]})"
  PREREQ_FAIL=true
fi

# Check whiptail
if ! command -v whiptail &>/dev/null; then
  warn "whiptail not found — falling back to plain text mode"
  UI_WHIPTAIL=false
fi

# Check opencode or claude
if command -v opencode &>/dev/null; then
  AGENT_BIN="opencode"
  log "Found opencode at $(command -v opencode)"
elif command -v claude &>/dev/null; then
  AGENT_BIN="claude"
  log "Found Claude Code at $(command -v claude)"
else
  AGENT_BIN=""
  warn "Neither opencode nor claude found in PATH"
  warn "Install opencode: see https://opencode.ai"
fi

# Check git
if command -v git &>/dev/null; then
  log "Found git: $(git --version | head -1)"
else
  warn "git not found — updates via 'ecc update' disabled"
fi

# Check MCP
if detect_mcp; then
  log "Found codebase-memory-mcp at $MCP_BIN"
else
  info "codebase-memory-mcp not detected — install separately"
fi

echo ""

if $PREREQ_FAIL; then
  msgbox "Prerequisites Failed" \
"Some prerequisites are missing. Please fix them and re-run:

  • bash >= 4

After installing, run ./install.sh again."
  exit 1
fi

# ──────────────── STEP: Select mode ────────────────

MODE=""
if yesno "Installation Mode" \
"Do you want Quickstart mode?

  [Yes] = Quickstart — minimal prompts, optimized for AI-assisted use
  [No]  = Manual — full control over every option"; then
  MODE="quickstart"
  infobox "Mode" "Quickstart selected — you'll be asked minimal questions"
else
  MODE="manual"
  infobox "Mode" "Manual selected — full configuration wizard"
fi

# ──────────────── STEP: Configuration ────────────────

# Always ask for these
USER_NAME=$(inputbox "User" "Enter your name or alias (for config headers):" "${USER:-user}")
GITHUB_HANDLE=$(inputbox "GitHub" "Enter your GitHub username (optional):" "")

# Component selection (always install core + skills)
if [[ "$MODE" == "manual" ]]; then
  CHOICES=$(
    checklist "Components" \
"Select components to install:" 18 65 8 \
  "CONFIG"  "Core configuration files" ON \
  "SKILLS"  "All 33 ECC skills" ON \
  "MCP"     "MCP server config (codebase-memory)" ON \
  "COMMANDS" "Custom commands (/graph-brain)" ON \
  "LIBS"    "Shared libraries (lib/)" ON
  )
else
  # Quickstart: install everything
  CHOICES="CONFIG SKILLS MCP COMMANDS LIBS"
fi

# Custom paths (manual only)
if [[ "$MODE" == "manual" ]]; then
  CONFIG_DIR=$(inputbox "Config path" "opencode config directory:" "$OPENCODE_CONFIG")
  SKILLS_DIR=$(inputbox "Skills path" "Skills directory:" "$OPENCODE_SKILLS")
else
  CONFIG_DIR="$OPENCODE_CONFIG"
  SKILLS_DIR="$OPENCODE_SKILLS"
fi

# ──────────────── STEP: Install ────────────────

SKILL_COUNT=$(count_dirs "$REPO_DIR/skills" 1)
INSTALL_STEPS=0
echo "$CHOICES" | grep -q "CONFIG"   && INSTALL_STEPS=$((INSTALL_STEPS + 4))
echo "$CHOICES" | grep -q "SKILLS"   && INSTALL_STEPS=$((INSTALL_STEPS + SKILL_COUNT + 1))
echo "$CHOICES" | grep -q "MCP"      && INSTALL_STEPS=$((INSTALL_STEPS + 1))
echo "$CHOICES" | grep -q "COMMANDS" && INSTALL_STEPS=$((INSTALL_STEPS + 1))
echo "$CHOICES" | grep -q "LIBS"     && INSTALL_STEPS=$((INSTALL_STEPS + 3))

CURRENT_STEP=0
do_step() {
  CURRENT_STEP=$((CURRENT_STEP + 1))
  local pct=$((CURRENT_STEP * 100 / INSTALL_STEPS))
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    echo "XXX"
    echo "$pct"
    echo "$1"
    echo "XXX"
  else
    echo -e "  [${pct}%] $1"
  fi
}

# Start progress gauge
if [[ "$UI_WHIPTAIL" == "true" ]]; then
  exec 3>&1
  exec 1>/dev/null
  (
    # Gauge loop
    local pct=0
    while read -r line; do
      if [[ "$line" =~ ^[0-9]+$ ]]; then
        pct=$line
      fi
    done
  ) | whiptail --title "Installing" --gauge "" 8 60 0 &
  GAUGE_PID=$!
  exec 4>&1
fi

report_progress() {
  local pct=$1
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    echo "$pct"
  fi
}

# Create directories
infobox "Preparing" "Creating directories..."
mkdir -p "$CONFIG_DIR/commands"
mkdir -p "$SKILLS_DIR"
mkdir -p "$LOCAL_BIN"

# Backup existing
if [ -d "$CONFIG_DIR" ]; then
  bk=$(backup_dir "$CONFIG_DIR")
  info "Backup created: $bk"
fi

# Install config
if echo "$CHOICES" | grep -q "CONFIG"; then
  do_step "Installing core configuration..."
  cp "$REPO_DIR/config/opencode.jsonc" "$CONFIG_DIR/opencode.jsonc"
  do_step "Installing MCP config..."
  cp "$REPO_DIR/config/opencode.json" "$CONFIG_DIR/opencode.json"
  do_step "Installing methodology..."
  cp "$REPO_DIR/config/INSTRUCTIONS.md" "$CONFIG_DIR/INSTRUCTIONS.md"
  do_step "Installing agent rules..."
  cp "$REPO_DIR/config/AGENTS.md" "$CONFIG_DIR/AGENTS.md"
  log "Config installed to $CONFIG_DIR"
fi

# Install skills
if echo "$CHOICES" | grep -q "SKILLS" && [ -d "$REPO_DIR/skills" ]; then
  SKILL_COUNT=$(count_dirs "$REPO_DIR/skills" 1)
  if [ "$SKILL_COUNT" -gt 0 ]; then
    do_step "Preparing skills directory..."
    mkdir -p "$SKILLS_DIR"
    local i=0
    for skill_dir in "$REPO_DIR/skills"/*/; do
      [ -d "$skill_dir" ] || continue
      skill_name=$(basename "$skill_dir")
      i=$((i + 1))
      do_step "Installing skill $i/$SKILL_COUNT: $skill_name"
      target="$SKILLS_DIR/$skill_name"
      mkdir -p "$target"
      cp -r "$skill_dir"/* "$target/"
    done
    find "$SKILLS_DIR" \( -name "*.sh" -o -name "*.mjs" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
    log "$SKILL_COUNT skills installed to $SKILLS_DIR"
  fi
fi

# Install MCP config
if echo "$CHOICES" | grep -q "MCP"; then
  do_step "Configuring MCP servers..."
  cp "$REPO_DIR/config/opencode.json" "$CONFIG_DIR/opencode.json" 2>/dev/null || true
  log "MCP config installed"
fi

# Install commands
if echo "$CHOICES" | grep -q "COMMANDS"; then
  do_step "Installing custom commands..."
  if ls "$REPO_DIR/config/commands/"*.md &>/dev/null; then
    cp "$REPO_DIR/config/commands/"*.md "$CONFIG_DIR/commands/"
  fi
  log "Commands installed"
fi

# Install libraries
if echo "$CHOICES" | grep -q "LIBS"; then
  do_step "Installing UI library..."
  mkdir -p "$CONFIG_DIR/lib"
  cp "$REPO_DIR/lib/ui.sh" "$CONFIG_DIR/lib/ui.sh"
  do_step "Installing paths library..."
  cp "$REPO_DIR/lib/paths.sh" "$CONFIG_DIR/lib/paths.sh"
  do_step "Installing utils library..."
  cp "$REPO_DIR/lib/utils.sh" "$CONFIG_DIR/lib/utils.sh"
  log "Libraries installed to $CONFIG_DIR/lib/"
fi

# Install ecc CLI
do_step "Installing ecc CLI..."
cp "$REPO_DIR/ecc" "$LOCAL_BIN/ecc"
chmod +x "$LOCAL_BIN/ecc"
log "ecc CLI installed to $LOCAL_BIN/ecc"

# Copy scripts
do_step "Installing management scripts..."
mkdir -p "$CONFIG_DIR/scripts"
for script in configure.sh uninstall.sh; do
  if [ -f "$REPO_DIR/scripts/$script" ]; then
    cp "$REPO_DIR/scripts/$script" "$CONFIG_DIR/scripts/$script"
    chmod +x "$CONFIG_DIR/scripts/$script"
  fi
done

# Copy templates
if [ -d "$REPO_DIR/templates" ]; then
  mkdir -p "$CONFIG_DIR/templates"
  cp -r "$REPO_DIR/templates/"* "$CONFIG_DIR/templates/" 2>/dev/null || true
fi

# ──────────────── STEP: Post-install ────────────────

# PATH warning
PATH_WARN=""
if ! in_path "$LOCAL_BIN"; then
  PATH_WARN="\n  • Add $LOCAL_BIN to your PATH:\n    export PATH=\"\$PATH:$LOCAL_BIN\""
  # Suggest adding to shell rc
  warn "$LOCAL_BIN not in PATH"
fi

# MCP status
if detect_mcp; then
  MCP_STATUS="${C_GREEN}✓${C_NC} codebase-memory-mcp"
else
  MCP_STATUS="${C_YELLOW}⚠${C_NC} codebase-memory-mcp (install manually)"
fi

# ──────────────── STEP: Summary ────────────────

do_step "Finalizing..."

SUMMARY="Installation complete!

  Config: $CONFIG_DIR
  Skills: $SKILLS_DIR ($SKILL_COUNT)
  CLI:    $LOCAL_BIN/ecc
  MCP:    $MCP_STATUS
  Agent:  $AGENT_BIN
  $([[ -n "$GITHUB_HANDLE" ]] && echo "  User:   $USER_NAME ($GITHUB_HANDLE)" || echo "  User:   $USER_NAME")
$([[ -n "$PATH_WARN" ]] && echo "$PATH_WARN")

Next steps:
  • Run 'ecc doctor' to verify the installation
  • Run 'ecc status' to see what's installed
  • Read INSTRUCTIONS.md for the engineering methodology
  • Tell your AI agent to read the instructions"

if [[ "$UI_WHIPTAIL" == "true" ]]; then
  exec 1>&3 3>&-
  kill "$GAUGE_PID" 2>/dev/null || true
  print_banner
fi

echo ""
msgbox "Summary" "$SUMMARY"

# ──────────────── STEP: Next steps ────────────────

echo ""
if [[ "$MODE" == "quickstart" ]]; then
  echo -e "${C_CYAN}${C_BOLD}══════════════════════════════════════════${C_NC}"
  echo -e "${C_CYAN}${C_BOLD}  ✨ Ready for AI-assisted setup${C_NC}"
  echo -e "${C_CYAN}${C_BOLD}══════════════════════════════════════════${C_NC}"
  echo ""
  echo "  Your configuration is ready!"
  echo ""
  if [[ -n "$AGENT_BIN" ]]; then
    echo "  Start a session:"
    echo "    ${C_BOLD}$AGENT_BIN${C_NC}"
    echo ""
    echo "  The agent will automatically load the instructions"
    echo "  and methodology from the installed config."
  fi
else
  echo -e "${C_CYAN}${C_BOLD}══════════════════════════════════════════${C_NC}"
  echo -e "${C_CYAN}${C_BOLD}  Manual setup complete${C_NC}"
  echo -e "${C_CYAN}${C_BOLD}══════════════════════════════════════════${C_NC}"
  echo ""
  echo "  All components installed per your selections."
fi

echo ""
echo -e "${C_BOLD}Available commands:${C_NC}"
echo -e "  ${C_GREEN}ecc doctor${C_NC}     — Diagnostic check"
echo -e "  ${C_GREEN}ecc status${C_NC}    — Installation status"
echo -e "  ${C_GREEN}ecc configure${C_NC} — Re-run configuration"
echo -e "  ${C_GREEN}ecc validate${C_NC}  — Verify integrity"
echo -e "  ${C_GREEN}ecc uninstall${C_NC} — Remove configuration"
echo -e "  ${C_GREEN}ecc update${C_NC}    — Pull latest version"
echo ""

if [[ -n "$PATH_WARN" ]]; then
  echo -e "${C_YELLOW}$PATH_WARN${C_NC}"
  echo ""
fi
