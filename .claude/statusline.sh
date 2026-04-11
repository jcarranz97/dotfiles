#!/usr/bin/env bash
# Claude Code status line
# Each section is a self-contained function. Customize emojis and toggle
# sections on/off in the CONFIGURATION block below.

# ============================================================
# CONFIGURATION
# ============================================================
SHOW_CWD=true          ; EMOJI_CWD="📁"
SHOW_MODEL=true        ; EMOJI_MODEL="🤖"
SHOW_CONTEXT=true      ; EMOJI_CONTEXT="🔋"
SHOW_COST=true         ; EMOJI_COST="💰"
SHOW_DURATION=false     ; EMOJI_DURATION="⏱"
SHOW_RATE_LIMITS=true  ; EMOJI_RATE="⚡"  ; EMOJI_RESET="🔄"
SHOW_STOCK=true        ; EMOJI_STOCK="📈"

# Stock settings
# Stocks are defined in STATUSLINE_DATA — add/remove tickers there
STATUSLINE_DATA="$HOME/.claude_statusline.json"
STOCK_REFRESH_TTL=300   # seconds between price refresh attempts
STOCK_STALE_TTL=3600    # seconds before showing a stale warning (⚠️)

# ============================================================
# REQUIRED TOOLS
# ============================================================
REQUIRED_TOOLS=("jq" "curl")
missing=()
for tool in "${REQUIRED_TOOLS[@]}"; do
  command -v "$tool" &>/dev/null || missing+=("$tool")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Status bar error: missing tools: ${missing[*]} — install them to enable the status bar"
  exit 0
fi

# ============================================================
# COLORS  (real ESC bytes via $'...' — safe to embed anywhere)
# ============================================================
RESET=$'\033[0m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
STRIKETHROUGH=$'\033[9m'
CYAN=$'\033[36m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
MAGENTA=$'\033[35m'

# ============================================================
# HELPERS
# ============================================================

# pick_color <int>  →  echoes the color variable for a percentage value
pick_color() {
  local int=$1
  if   [ "$int" -ge 90 ]; then echo "$RED"
  elif [ "$int" -ge 70 ]; then echo "$YELLOW"
  else echo "$GREEN"
  fi
}

# render_bar <int>  →  echoes a 10-block █░ progress bar
render_bar() {
  local int=$1
  local filled=$(( int / 10 ))
  local empty=$(( 10 - filled ))
  local bar=""
  for _ in $(seq 1 $filled); do bar="${bar}█"; done
  for _ in $(seq 1 $empty);  do bar="${bar}░"; done
  echo "$bar"
}

# format_countdown <seconds>  →  echoes the 2 most significant non-zero units
# Examples: 6d 2h 20m → "6d 2h" | 2h 10m → "2h 10m" | 20m → "20m"
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

# ============================================================
# SECTIONS
# ============================================================

section_cwd() {
  local cwd short branch branch_part
  cwd=$(echo "$input" | jq -r '.cwd // "?"')
  short=$(sed "s|^/home/$USER|~|" <<< "$cwd")
  branch=$(git -C "$cwd" branch --show-current 2>/dev/null)
  [ -n "$branch" ] && branch_part="${MAGENTA}  ${branch}${RESET}" || branch_part=""
  echo "${EMOJI_CWD} ${CYAN}${short}${RESET}${branch_part}"
}

section_model() {
  local model
  model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
  echo "${EMOJI_MODEL} ${DIM}${model}${RESET}"
}

section_context() {
  local pct int color bar
  pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
  int=${pct%.*}
  color=$(pick_color "$int")
  bar=$(render_bar "$int")
  echo "${EMOJI_CONTEXT} ${color}${bar}${RESET} ${int}%"
}

section_cost() {
  local total
  total=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
  printf "%s ${YELLOW}\$%.4f${RESET}" "$EMOJI_COST" "$total"
}

section_duration() {
  local ms elapsed h m s
  ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
  elapsed=$(( ms / 1000 ))
  h=$(( elapsed / 3600 ))
  m=$(( (elapsed % 3600) / 60 ))
  s=$(( elapsed % 60 ))
  printf "%s %02d:%02d:%02d" "$EMOJI_DURATION" "$h" "$m" "$s"
}

section_rate_limits() {
  local five_h_pct five_h_reset seven_d_pct seven_d_reset result=""

  five_h_pct=$(echo "$input"   | jq -r '.rate_limits.five_hour.used_percentage // empty')
  five_h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  seven_d_pct=$(echo "$input"  | jq -r '.rate_limits.seven_day.used_percentage // empty')
  seven_d_reset=$(echo "$input"| jq -r '.rate_limits.seven_day.resets_at // empty')

  [ -z "$five_h_pct" ] && [ -z "$seven_d_pct" ] && return

  if [ -n "$five_h_pct" ]; then
    local int color reset_str=""
    int=${five_h_pct%.*}
    color=$(pick_color "$int")
    [ -n "$five_h_reset" ] && reset_str=" (${EMOJI_RESET} $(format_countdown $(( five_h_reset - now ))))"
    result="${EMOJI_RATE} 5h: ${color}${int}%${RESET}${reset_str}"
  fi

  if [ -n "$seven_d_pct" ]; then
    local int color reset_str=""
    int=${seven_d_pct%.*}
    color=$(pick_color "$int")
    [ -n "$seven_d_reset" ] && reset_str=" (${EMOJI_RESET} $(format_countdown $(( seven_d_reset - now ))))"
    [ -n "$result" ] && result+="  "
    result+="7d: ${color}${int}%${RESET}${reset_str}"
  fi

  echo "$result"
}

section_stock() {
  [ -f "$STATUSLINE_DATA" ] || return

  local tickers result="" ticker price last_updated age new_price tmp

  tickers=$(jq -r '.stocks | keys[]' "$STATUSLINE_DATA" 2>/dev/null)
  [ -z "$tickers" ] && return

  while IFS= read -r ticker; do
    price=$(jq -r ".stocks[\"$ticker\"].price // empty" "$STATUSLINE_DATA")
    last_updated=$(jq -r ".stocks[\"$ticker\"].last_updated // 0" "$STATUSLINE_DATA")
    age=$(( now - last_updated ))

    # Attempt refresh if older than STOCK_REFRESH_TTL
    if [ "$age" -gt "$STOCK_REFRESH_TTL" ]; then
      new_price=$(curl -s --max-time 3 \
        "https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=1d" \
        | jq -r '.chart.result[0].meta.regularMarketPrice // empty' 2>/dev/null)
      if [ -n "$new_price" ]; then
        tmp=$(mktemp)
        jq --arg t "$ticker" --argjson p "$new_price" --argjson ts "$now" \
          '.stocks[$t].price = $p | .stocks[$t].last_updated = $ts' \
          "$STATUSLINE_DATA" > "$tmp" && mv "$tmp" "$STATUSLINE_DATA"
        price="$new_price"
        age=0
      fi
    fi

    [ -z "$price" ] && continue

    # Build per-ticker entry
    local entry
    if [ "$age" -gt "$STOCK_STALE_TTL" ]; then
      entry=$(printf "%s ${STRIKETHROUGH}${YELLOW}\$%.2f${RESET} (⚠️$(format_countdown $age) ago)" "$ticker" "$price")
    else
      entry=$(printf "%s ${YELLOW}\$%.2f${RESET}" "$ticker" "$price")
    fi

    [ -n "$result" ] && result+="  "
    result+="$entry"
  done <<< "$tickers"

  [ -z "$result" ] && return
  echo "${EMOJI_STOCK} ${result}"
}

# ============================================================
# ASSEMBLE
# ============================================================
input=$(cat)
now=$(date +%s)

parts=()
$SHOW_CWD         && parts+=("$(section_cwd)")
$SHOW_MODEL       && parts+=("$(section_model)")
$SHOW_CONTEXT     && parts+=("$(section_context)")
$SHOW_COST        && parts+=("$(section_cost)")
$SHOW_DURATION    && parts+=("$(section_duration)")
$SHOW_RATE_LIMITS && { r=$(section_rate_limits); [ -n "$r" ] && parts+=("$r"); }
$SHOW_STOCK       && { s=$(section_stock);        [ -n "$s" ] && parts+=("$s"); }

# Join non-empty parts with double-space separator
out=""
for part in "${parts[@]}"; do
  [ -n "$out" ] && out+="  "
  out+="$part"
done
printf "%s\n" "$out"
