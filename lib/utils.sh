# utils.sh — Common utilities for opencode config manager
# Source this file, don't execute it: source lib/utils.sh

setup_utils() {
  [[ -n "${UTILS_SETUP:-}" ]] && return 0
  UTILS_SETUP=true
}

log()  { echo -e "${C_GREEN}✓${C_NC} $1"; }
info() { echo -e "${C_CYAN}→${C_NC} $1"; }
warn() { echo -e "${C_YELLOW}⚠${C_NC} $1"; }
error(){ echo -e "${C_RED}✗${C_NC} $1"; }

backup_dir() {
  local src="$1"
  local ts; ts=$(date +%Y%m%d%H%M%S)
  local dst="${src}.bak.${ts}"
  if [ -d "$src" ] || [ -f "$src" ]; then
    cp -r "$src" "$dst"
    echo "$dst"
    return 0
  fi
  return 1
}

os_name() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)  echo "linux" ;;
    MINGW*|MSYS*) echo "windows" ;;
    *)      echo "unknown" ;;
  esac
}

is_macos()  { [[ "$(os_name)" == "macos" ]] && return 0 || return 1; }
is_linux()  { [[ "$(os_name)" == "linux" ]] && return 0 || return 1; }

require_whiptail() {
  if ! command -v whiptail &>/dev/null; then
    echo "whiptail is required but not installed."
    case "$(os_name)" in
      linux)  echo "Install: sudo apt install whiptail  (or: sudo pacman -S libnewt)" ;;
      macos)  echo "Install: brew install newt" ;;
    esac
    return 1
  fi
}

check_command() {
  local cmd="$1" pkg="${2:-$1}"
  if command -v "$cmd" &>/dev/null; then
    return 0
  else
    return 1
  fi
}

count_dirs() {
  local base="$1" maxdepth="${2:-1}"
  if [ -d "$base" ]; then
    find "$base" -mindepth 1 -maxdepth "$maxdepth" -type d 2>/dev/null | wc -l
  else
    echo 0
  fi
}
