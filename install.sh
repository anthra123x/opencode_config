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

# ─── 1. Instalar configuración ─────────────────────────
info "Instalando configuración..."
mkdir -p "$OPENCODE_CONFIG/commands"

cp "$REPO_DIR/config/opencode.jsonc"  "$OPENCODE_CONFIG/opencode.jsonc"
cp "$REPO_DIR/config/opencode.json"   "$OPENCODE_CONFIG/opencode.json"
cp "$REPO_DIR/config/INSTRUCTIONS.md" "$OPENCODE_CONFIG/INSTRUCTIONS.md"
cp "$REPO_DIR/config/AGENTS.md"       "$OPENCODE_CONFIG/AGENTS.md"

if ls "$REPO_DIR/config/commands/"*.md &>/dev/null 2>&1; then
  cp "$REPO_DIR/config/commands/"*.md "$OPENCODE_CONFIG/commands/"
fi

log "Configuración instalada en $OPENCODE_CONFIG"

# ─── 2. Instalar skills ────────────────────────────────
if [ -d "$REPO_DIR/skills" ]; then
  info "Instalando skills..."
  mkdir -p "$OPENCODE_SKILLS"
  count=0
  for skill_dir in "$REPO_DIR/skills"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    target="$OPENCODE_SKILLS/$skill_name"
    mkdir -p "$target"
    cp -r "$skill_dir"/* "$target/"
    count=$((count + 1))
  done
  log "$count skills instalados en $OPENCODE_SKILLS"
fi

# ─── 3. Resumen ────────────────────────────────────────
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

skill_count=$(find "$OPENCODE_SKILLS" -maxdepth 1 -type d | wc -l)
skill_count=$((skill_count - 1)) # subtract parent dir
echo ""
echo "  Skills: $skill_count"
echo ""

warn "Ya instalado en ~/.opencode/skills/ — si ya tenías skills, se sobrescribieron."
echo ""
echo -e "${YELLOW}  Siguiente paso recomendado:${NC}"
echo "    Revisa INSTRUCTIONS.md para entender la metodología y los skills disponibles."
echo ""
