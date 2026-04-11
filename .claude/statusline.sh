#!/usr/bin/env bash
# Claude Code status line script
# Displays: model name, context window usage with progress bar, session cost, session duration

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

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')

# --- Context window ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
used_int=${used_pct%.*}
bar_filled=$(( used_int / 10 ))
bar_empty=$(( 10 - bar_filled ))
bar=""
for i in $(seq 1 $bar_filled); do bar="${bar}#"; done
for i in $(seq 1 $bar_empty);  do bar="${bar}-"; done
ctx_str="[${bar}] ${used_int}%"

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

# --- Output ---
printf '%s  ctx %s  cost %s  dur %s\n' "$model" "$ctx_str" "$cost_str" "$duration_str"
