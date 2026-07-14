# ui.sh — Terminal UI Library
# Provides whiptail-based TUI with plain-text fallback
# Source this file, don't execute it: source lib/ui.sh

setup_ui() {
  [[ -n "${UI_SETUP:-}" ]] && return 0

  if command -v whiptail &>/dev/null && [[ -t 1 ]]; then
    UI_WHIPTAIL=true
  else
    UI_WHIPTAIL=false
  fi

  if command -v tput &>/dev/null && [[ -t 1 ]]; then
    C_RED=$(tput setaf 1)    C_GREEN=$(tput setaf 2)
    C_YELLOW=$(tput setaf 3) C_BLUE=$(tput setaf 4)
    C_MAGENTA=$(tput setaf 5) C_CYAN=$(tput setaf 6)
    C_BOLD=$(tput bold)      C_DIM=$(tput dim)
    C_NC=$(tput sgr0)
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
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --msgbox "$msg" "$h" "$w"
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg\n"
    read -rp "Press Enter to continue... " _
  fi
}

yesno() {
  local title="$1" msg="$2"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --yesno "$msg" 12 60
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg"
    read -rp "[Y/n] " _ans
    [[ "$_ans" =~ ^[Yy] ]] && return 0 || return 1
  fi
}

inputbox() {
  local title="$1" msg="$2" default="${3:-}"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --inputbox "$msg" 10 60 "$default" 3>&1 1>&2 2>&3
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg"
    read -rp "> " _val
    echo "${_val:-$default}"
  fi
}

passwordbox() {
  local title="$1" msg="$2"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --passwordbox "$msg" 10 60 3>&1 1>&2 2>&3
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg"
    read -rsp "> " _val; echo
    echo "$_val"
  fi
}

radiolist() {
  local title="$1" msg="$2" h="${3:-15}" w="${4:-50}" list_h="${5:-8}"
  shift 5
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --radiolist "$msg" "$h" "$w" "$list_h" "$@"
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg"
    local i=0; local -a _opts=()
    while [[ $# -gt 2 ]]; do
      i=$((i+1))
      echo "  $i) $1  ($2)"
      _opts+=("$i")
      shift 3
    done
    read -rp "Choice: " _sel
    echo "${_opts[$((_sel-1))]}"
  fi
}

checklist() {
  local title="$1" msg="$2" h="${3:-18}" w="${4:-60}" list_h="${5:-10}"
  shift 5
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --checklist "$msg" "$h" "$w" "$list_h" "$@"
    return $?
  else
    echo -e "\n${C_BOLD}═══ $title ═══${C_NC}\n$msg"
    local i=0
    while [[ $# -gt 2 ]]; do
      i=$((i+1))
      local _status=" "
      [[ "$3" == "ON" ]] && _status="*"
      echo "  $_status $i) $1  ($2)"
      shift 3
    done
    echo "(Enter item numbers separated by space)"
    read -rp "> " _sels
    echo "$_sels"
  fi
}

infobox() {
  local title="$1" msg="$2"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --infobox "$msg" 6 60
  else
    echo -e "${C_CYAN}→${C_NC} $msg"
  fi
}

textbox() {
  local title="$1" file="$2" h="${3:-20}" w="${4:-70}"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --textbox "$file" "$h" "$w"
  else
    cat "$file"
  fi
}

gauge() {
  local title="$1" msg="$2" h="${3:-8}" w="${4:-60}"
  if [[ "$UI_WHIPTAIL" == "true" ]]; then
    _wt --title "$title" --gauge "$msg" "$h" "$w"
  else
    echo "$msg"
  fi
}

print_banner() {
  echo -e "${C_CYAN}${C_BOLD}"
  echo '  ╔══════════════════════════════════════╗'
  echo '  ║       opencode Configuration         ║'
  echo '  ║          📦 ECC Manager v1           ║'
  echo '  ╚══════════════════════════════════════╝'
  echo -e "${C_NC}"
}
