# paths.sh — Path resolution for opencode config
# Source this file, don't execute it: source lib/paths.sh

setup_paths() {
  [[ -n "${PATHS_SETUP:-}" ]] && return 0

  OPENCODE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  OPENCODE_SKILLS="${OPENCODE_SKILLS:-$HOME/.opencode/skills}"
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
