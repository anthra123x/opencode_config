# paths.sh — Path resolution and environment detection for opencode config
# Source this file, don't execute it: source lib/paths.sh

setup_paths() {
  [[ -n "${PATHS_SETUP:-}" ]] && return 0

  OPENCODE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  OPENCODE_SKILLS="${OPENCODE_SKILLS:-$HOME/.opencode/skills}"
  OPENCODE_AGENTS="${OPENCODE_CONFIG}/agents"
  OPENCODE_COMMANDS="${OPENCODE_CONFIG}/commands"
  OPENCODE_MCP="${OPENCODE_CONFIG}/mcp"
  OPENCODE_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/opencode"
  LOCAL_BIN="${HOME}/.local/bin"

  PATHS_SETUP=true
}

detect_opencode() {
  if command -v opencode &>/dev/null; then
    OPENCODE_BIN=$(command -v opencode)
    return 0
  elif command -v claude &>/dev/null; then
    OPENCODE_BIN=$(command -v claude)
    return 0
  fi
  return 1
}

detect_python() {
  if command -v python3 &>/dev/null; then
    PYTHON_BIN=$(command -v python3)
    return 0
  fi
  return 1
}

detect_sqlite_fts5() {
  if command -v python3 &>/dev/null; then
    if python3 -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.execute('CREATE VIRTUAL TABLE t USING fts5(c)')" &>/dev/null; then
      return 0
    fi
  fi
  return 1
}

detect_mcp() {
  if command -v codebase-memory-mcp &>/dev/null; then
    MCP_BIN=$(command -v codebase-memory-mcp)
    return 0
  fi
  return 1
}

detect_whiptail() {
  command -v whiptail &>/dev/null && return 0 || return 1
}

in_path() {
  local dir="${1:-$LOCAL_BIN}"
  case ":$PATH:" in
    *:"$dir":*) return 0 ;;
    *) return 1 ;;
  esac
}
