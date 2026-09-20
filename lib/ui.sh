# ui.sh — Terminal UI Library
# Provides whiptail-based TUI with plain-text fallback
# Source this file, don't execute it: source lib/ui.sh

setup_ui() {
  [[ -n "${UI_SETUP:-}" ]] && return 0

  # Test if whiptail actually works in this terminal environment
  if command -v whiptail &>/dev/null && whiptail --infobox "test" 5 20 2>/dev/null; then
    UI_WHIPTAIL=true
  else
    UI_WHIPTAIL=false
  fi

  if command -v tput &>/dev/null && tput setaf 1 &>/dev/null; then
    C_RED=$(tput setaf 1 2>/dev/null || echo "")
    C_GREEN=$(tput setaf 2 2>/dev/null || echo "")
    C_YELLOW=$(tput setaf 3 2>/dev/null || echo "")
    C_BLUE=$(tput setaf 4 2>/dev/null || echo "")
    C_MAGENTA=$(tput setaf 5 2>/dev/null || echo "")
    C_CYAN=$(tput setaf 6 2>/dev/null || echo "")
    C_BOLD=$(tput bold 2>/dev/null || echo "")
    C_DIM=$(tput dim 2>/dev/null || echo "")
    C_NC=$(tput sgr0 2>/dev/null || echo "")
  else
    C_RED='' C_GREEN='' C_YELLOW='' C_BLUE=''
    C_MAGENTA='' C_CYAN='' C_BOLD='' C_DIM='' C_NC=''
  fi

  UI_SETUP=true
}

_wt() {
  whiptail "$@"
  return $?
}

msgbox() {
  local title="$1" msg="$2" h="${3:-15}" w="${4:-60}"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --msgbox "$msg" "$h" "$w"
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg\n" >&2
    if [[ -t 0 ]]; then
      read -rp "Press Enter to continue... " _ >&2 || true
    fi
  fi
}

yesno() {
  local title="$1" msg="$2"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --yesno "$msg" 12 60
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg" >&2
    if [[ -t 0 ]]; then
      read -rp "[Y/n] " _ans >&2 || _ans="y"
      [[ "$_ans" =~ ^[Yy] ]] && return 0 || return 1
    else
      return 0
    fi
  fi
}

inputbox() {
  local title="$1" msg="$2" default="${3:-}"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --inputbox "$msg" 10 60 "$default" 3>&1 1>&2 2>&3
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg" >&2
    if [[ -t 0 ]]; then
      read -rp "> " _val >&2 || _val=""
      echo "${_val:-$default}"
    else
      echo "$default"
    fi
  fi
}

passwordbox() {
  local title="$1" msg="$2"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --passwordbox "$msg" 10 60 3>&1 1>&2 2>&3
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg" >&2
    if [[ -t 0 ]]; then
      read -rsp "> " _val >&2; echo >&2
      echo "$_val"
    else
      echo ""
    fi
  fi
}

radiolist() {
  local title="$1" msg="$2" h="${3:-15}" w="${4:-50}" list_h="${5:-8}"
  shift 5
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --radiolist "$msg" "$h" "$w" "$list_h" "$@"
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg" >&2
    local i=0; local -a _opts=()
    while [[ $# -gt 2 ]]; do
      i=$((i+1))
      echo "  $i) $1  ($2)" >&2
      _opts+=("$1")
      shift 3
    done
    if [[ -t 0 ]]; then
      read -rp "Choice: " _sel >&2 || _sel=1
      echo "${_opts[$((_sel-1))]:-${_opts[0]}}"
    else
      echo "${_opts[0]}"
    fi
  fi
}

checklist() {
  local title="$1" msg="$2" h="${3:-18}" w="${4:-60}" list_h="${5:-10}"
  shift 5
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --checklist "$msg" "$h" "$w" "$list_h" "$@"
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg" >&2
    local i=0; local -a _items=()
    while [[ $# -gt 2 ]]; do
      i=$((i+1))
      local _status=" "
      [[ "$3" == "ON" ]] && _status="*"
      echo "  $_status $i) $1  ($2)" >&2
      _items+=("$1")
      shift 3
    done
    if [[ -t 0 ]]; then
      echo "(Enter item numbers separated by space, or press Enter for all)" >&2
      read -rp "> " _sels >&2 || _sels=""
      if [[ -z "$_sels" ]]; then
        echo "${_items[*]}"
      else
        local -a _res=()
        for idx in $_sels; do
          _res+=("${_items[$((idx-1))]}")
        done
        echo "${_res[*]}"
      fi
    else
      echo "${_items[*]}"
    fi
  fi
}

infobox() {
  local title="$1" msg="$2"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --infobox "$msg" 6 60
  else
    echo -e "${C_CYAN}→${C_NC} $msg" >&2
  fi
}

textbox() {
  local title="$1" file="$2" h="${3:-20}" w="${4:-70}"
  if [[ "${UI_WHIPTAIL:-false}" == "true" ]]; then
    _wt --title "$title" --textbox "$file" "$h" "$w"
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n" >&2
    cat "$file" >&2
    echo "" >&2
  fi
}

print_banner() {
  cat <<'BANNER'
  ╔══════════════════════════════════════════════════════════════╗
  ║                 OpenCode Swarm Suite v2.0                    ║
  ║       🛡️ Multi-Agent Architecture & Persistent Context        ║
  ╚══════════════════════════════════════════════════════════════╝
BANNER
}
