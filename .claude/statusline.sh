#!/usr/bin/env bash
# Claude Code status line script
# Displays: cwd, model name, context window usage with progress bar, session cost, session duration,
#           5-hour rate limit usage + reset time, 7-day rate limit usage + reset time

# --- Required tools ---
REQUIRED_TOOLS=("jq")
missing=()
for tool in "${REQUIRED_TOOLS[@]}"; do
  command -v "$tool" &>/dev/null || missing+=("$tool")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Status bar error: missing tools: ${missing[*]} — install them to enable the status bar"
  exit 0
fi

input=$(cat)

# --- Colors ---
RESET='\033[0m'
BOLD='\033[1m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'
MAGENTA='\033[35m'

# --- CWD ---
cwd=$(echo "$input" | jq -r '.cwd // "?"')
cwd_short=$(sed "s|^/home/$USER|~|" <<< "$cwd")

# --- Git branch ---
branch=$(git -C "$cwd" branch --show-current 2>/dev/null)
[ -n "$branch" ] && branch_str="  $branch" || branch_str=""

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')

# --- Context window (color changes based on usage) ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
used_int=${used_pct%.*}
bar_filled=$(( used_int / 10 ))
bar_empty=$(( 10 - bar_filled ))
bar=""
for i in $(seq 1 $bar_filled); do bar="${bar}█"; done
for i in $(seq 1 $bar_empty);  do bar="${bar}░"; done
if   [ "$used_int" -ge 90 ]; then bar_color="$RED"
elif [ "$used_int" -ge 70 ]; then bar_color="$YELLOW"
else bar_color="$GREEN"
fi

# --- Session cost ---
total_cost=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
cost_str=$(printf '$%.4f' "$total_cost")

# --- Session duration ---
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
elapsed=$(( duration_ms / 1000 ))
hrs=$(( elapsed / 3600 ))
mins=$(( (elapsed % 3600) / 60 ))
secs=$(( elapsed % 60 ))
duration_str=$(printf '%02d:%02d:%02d' "$hrs" "$mins" "$secs")

# --- Rate limits ---
five_h_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_d_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
seven_d_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

# format_countdown <seconds>
# Prints the 2 most significant non-zero units from: days, hours, minutes.
# Examples: 6d 2h 20m -> "6d 2h" | 0d 2h 10m -> "2h 10m" | 0h 20m -> "20m"
format_countdown() {
  local secs=$1
  [ "$secs" -lt 0 ] && secs=0
  local d=$(( secs / 86400 ))
  local h=$(( (secs % 86400) / 3600 ))
  local m=$(( (secs % 3600) / 60 ))
  local parts=()
  [ "$d" -gt 0 ] && parts+=("${d}d")
  [ "$h" -gt 0 ] && parts+=("${h}h")
  [ "$m" -gt 0 ] && parts+=("${m}m")
  [ "${#parts[@]}" -eq 0 ] && parts=("0m")
  echo "${parts[0]}${parts[1]:+ ${parts[1]}}"
}

# Build rate limit display only when data is available (Pro/Max accounts)
# Colors must be resolved via printf format string (not stored in vars passed as %s args)
now=$(date +%s)
rate_str=""
if [ -n "$five_h_pct" ]; then
  five_h_int=${five_h_pct%.*}
  if   [ "$five_h_int" -ge 90 ]; then five_h_color="$RED"
  elif [ "$five_h_int" -ge 70 ]; then five_h_color="$YELLOW"
  else five_h_color="$GREEN"
  fi
  five_h_reset_str=""
  [ -n "$five_h_reset" ] && five_h_reset_str=" (🔄 $(format_countdown $(( five_h_reset - now ))))"
  rate_str=$(printf " ⚡ 5h: ${five_h_color}%s%%${RESET}%s" "$five_h_int" "$five_h_reset_str")
fi

if [ -n "$seven_d_pct" ]; then
  seven_d_int=${seven_d_pct%.*}
  if   [ "$seven_d_int" -ge 90 ]; then seven_d_color="$RED"
  elif [ "$seven_d_int" -ge 70 ]; then seven_d_color="$YELLOW"
  else seven_d_color="$GREEN"
  fi
  seven_d_reset_str=""
  [ -n "$seven_d_reset" ] && seven_d_reset_str=" (🔄 $(format_countdown $(( seven_d_reset - now ))))"
  rate_str="${rate_str}$(printf "  7d: ${seven_d_color}%s%%${RESET}%s" "$seven_d_int" "$seven_d_reset_str")"
fi

# --- Output ---
printf "📁 ${CYAN}%s${RESET}${MAGENTA}%s${RESET}  🤖 ${DIM}%s${RESET}  🔋 ${bar_color}%s${RESET} ${used_int}%%  💰 ${YELLOW}%s${RESET}  ⏱ %s%s" \
  "$cwd_short" "$branch_str" "$model" "$bar" "$cost_str" "$duration_str" "$rate_str"
