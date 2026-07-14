#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
OPENCODE_SKILLS="$HOME/.opencode/skills"

# Portable colors
if command -v tput &>/dev/null && [[ -t 1 ]]; then
  RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
  RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

log()  { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

echo ""
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${CYAN}  opencode Configuration Installer${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""

# ─── 1. Respaldar configuración existente ──────────────
if [ -d "$OPENCODE_CONFIG" ]; then
  BACKUP_CONFIG="${OPENCODE_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"
  info "Respaldo de configuración: $BACKUP_CONFIG"
  cp -r "$OPENCODE_CONFIG" "$BACKUP_CONFIG"
fi

if [ -d "$OPENCODE_SKILLS" ]; then
  BACKUP_SKILLS="${OPENCODE_SKILLS}.bak.$(date +%Y%m%d%H%M%S)"
  info "Respaldo de skills: $BACKUP_SKILLS"
  cp -r "$OPENCODE_SKILLS" "$BACKUP_SKILLS"
fi

# ─── 2. Instalar configuración ─────────────────────────
info "Instalando configuración..."
mkdir -p "$OPENCODE_CONFIG/commands"

cp "$REPO_DIR/config/opencode.jsonc"  "$OPENCODE_CONFIG/opencode.jsonc"
cp "$REPO_DIR/config/opencode.json"   "$OPENCODE_CONFIG/opencode.json"
cp "$REPO_DIR/config/INSTRUCTIONS.md" "$OPENCODE_CONFIG/INSTRUCTIONS.md"
cp "$REPO_DIR/config/AGENTS.md"       "$OPENCODE_CONFIG/AGENTS.md"

if ls "$REPO_DIR/config/commands/"*.md &>/dev/null; then
  cp "$REPO_DIR/config/commands/"*.md "$OPENCODE_CONFIG/commands/"
fi

log "Configuración instalada en $OPENCODE_CONFIG"

# ─── 3. Instalar skills ────────────────────────────────
if [ -d "$REPO_DIR/skills" ]; then
  SKILL_COUNT=$(find "$REPO_DIR/skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
  if [ "$SKILL_COUNT" -eq 0 ]; then
    warn "No se encontraron skills en $REPO_DIR/skills/"
  else
    info "Instalando $SKILL_COUNT skills..."
    mkdir -p "$OPENCODE_SKILLS"
    for skill_dir in "$REPO_DIR/skills"/*/; do
      [ -d "$skill_dir" ] || continue
      skill_name=$(basename "$skill_dir")
      target="$OPENCODE_SKILLS/$skill_name"
      mkdir -p "$target"
      cp -r "$skill_dir"/* "$target/"
    done
    # Fix executable permissions on scripts
    find "$OPENCODE_SKILLS" \( -name "*.sh" -o -name "*.mjs" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
    log "$SKILL_COUNT skills instalados en $OPENCODE_SKILLS"
  fi
fi

# ─── 4. Resumen ────────────────────────────────────────
echo ""
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Instalación completa${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""

echo "  Configuración:"
for f in "$OPENCODE_CONFIG"/{opencode.jsonc,opencode.json,INSTRUCTIONS.md,AGENTS.md}; do
  [ -f "$f" ] && echo "    • $(basename "$f")"
done
for cmd in "$OPENCODE_CONFIG"/commands/*.md; do
  [ -f "$cmd" ] && echo "    • commands/$(basename "$cmd")"
done

INSTALLED_SKILLS=$(find "$OPENCODE_SKILLS" -mindepth 1 -maxdepth 1 -type d -not -name '.*' -not -name '*.bak.*' | wc -l)
echo ""
echo "  Skills: $INSTALLED_SKILLS"

echo ""
echo -e "${YELLOW}  Siguiente paso:${NC}"
echo "    Revisa INSTRUCTIONS.md para entender la metodología y los skills disponibles."
echo "    Para el MCP codebase-memory-mcp, asegúrate de que el binario esté en tu PATH."
echo ""
