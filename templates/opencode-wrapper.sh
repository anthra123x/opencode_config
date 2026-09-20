#!/usr/bin/env bash
# opencode — OpenCode Swarm Edition Launcher
# Wraps vanilla opencode with Swarm visual branding and terminal title

REAL_OPENCODE="/usr/bin/opencode"

if [ ! -x "$REAL_OPENCODE" ]; then
  REAL_OPENCODE=$(type -ap opencode | grep -v "$HOME/.local/bin/opencode" | head -n 1)
fi

# Set terminal title
if [[ -t 1 ]]; then
  echo -ne "\033]0;⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ]\007"
fi

# Print stylized banner when launching interactive TUI or without arguments
if [[ $# -eq 0 ]] || [[ "$1" =~ ^(-i|--interactive|run)$ ]]; then
  C_PURPLE="\033[38;5;141m"
  C_CYAN="\033[38;5;51m"
  C_BOLD="\033[1m"
  C_RESET="\033[0m"

  echo -e "${C_PURPLE}${C_BOLD}  ╭──────────────────────────────────────────────────────────────╮${C_RESET}"
  echo -e "${C_PURPLE}${C_BOLD}  │   ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫                              │${C_RESET}"
  echo -e "${C_PURPLE}${C_BOLD}  │   ${C_CYAN}🛡️  Multi-Agent Architecture & Persistent Context Memory    ${C_PURPLE}│${C_RESET}"
  echo -e "${C_PURPLE}${C_BOLD}  ╰──────────────────────────────────────────────────────────────╯${C_RESET}"
fi

exec "$REAL_OPENCODE" "$@"
