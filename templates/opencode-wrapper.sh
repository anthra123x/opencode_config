#!/usr/bin/env bash
# opencode — OpenCode Swarm Edition Launcher
# Wraps vanilla opencode with Swarm visual branding and terminal title

REAL_OPENCODE="/usr/bin/opencode"

if [ ! -x "$REAL_OPENCODE" ]; then
  REAL_OPENCODE=$(type -ap opencode | grep -v "$HOME/.local/bin/opencode" | head -n 1)
fi

# Ensure Web Cockpit & GetBrain monitoring server is running in background on port 4040
SERVER_SCRIPT="$HOME/.config/opencode/web/server.py"
if [ ! -f "$SERVER_SCRIPT" ]; then
  # Fallback to repo dir if run from repo
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [ -f "$REPO_DIR/web/server.py" ]; then
    SERVER_SCRIPT="$REPO_DIR/web/server.py"
  fi
fi

if [ -f "$SERVER_SCRIPT" ]; then
  # Check if port 4040 is listening; if not, launch in background
  if ! python3 -c "import socket; s = socket.socket(); s.settimeout(0.3); exit(s.connect_ex(('127.0.0.1', 4040)))" 2>/dev/null; then
    nohup python3 "$SERVER_SCRIPT" --port 4040 >/dev/null 2>&1 &
    disown 2>/dev/null || true
    # Brief yield so socket starts binding
    sleep 0.15
  fi
fi

# Set terminal title
if [[ -t 1 ]]; then
  echo -ne "\033]0;⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ]\007"
fi

# Launch OpenCode (the home tips section inside OpenCode displays the live server link)
exec "$REAL_OPENCODE" "$@"
