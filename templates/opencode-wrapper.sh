#!/usr/bin/env bash
# opencode — OpenCode Swarm Edition Launcher
# Wraps vanilla opencode with per-project Swarm Web Cockpit sessions and terminal branding

REAL_OPENCODE="/usr/bin/opencode"

if [ ! -x "$REAL_OPENCODE" ]; then
  REAL_OPENCODE=$(type -ap opencode | grep -v "$HOME/.local/bin/opencode" | head -n 1)
fi

# Detect project workspace directory and project name
PROJECT_DIR="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"

# Locate Swarm Web server script
SERVER_SCRIPT="$HOME/.config/opencode/web/server.py"
if [ ! -f "$SERVER_SCRIPT" ]; then
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [ -f "$REPO_DIR/web/server.py" ]; then
    SERVER_SCRIPT="$REPO_DIR/web/server.py"
  fi
fi

# Ensure dedicated web session & GetBrain monitoring server for this project
if [ -f "$SERVER_SCRIPT" ]; then
  SERVER_PORT=$(python3 "$SERVER_SCRIPT" --ensure --dir "$PROJECT_DIR" --project "$PROJECT_NAME" 2>/dev/null || echo "4040")
  if [ -n "$SERVER_PORT" ]; then
    export OPENCODE_WEB_PORT="$SERVER_PORT"
    export OPENCODE_WEB_URL="http://localhost:$SERVER_PORT"
  fi
fi

# Set terminal window title
if [[ -t 1 ]]; then
  echo -ne "\033]0;⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ] — ${PROJECT_NAME}\007"
fi

# Launch OpenCode (home tips and plugin display project-specific URL)
exec "$REAL_OPENCODE" "$@"
