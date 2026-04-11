# Claude Code Status Line

A live status bar displayed at the bottom of every Claude Code session. It updates after each assistant message and gives you at-a-glance visibility into your session health, usage limits, costs, and even stock prices — without ever leaving the terminal.

## What it shows

```
📁 ~/repos/dotfiles  main  🤖 Sonnet 4.6  🔋 ██░░░░░░░░ 16%  💰 $0.4888  ⚡ 5h: 10% (🔄2h 30m)  7d: 1% (🔄5d 14h)  📈 AMD $142.53
```

| Section | Example | Description |
|---|---|---|
| 📁 CWD | `📁 ~/repos/dotfiles` | Current working directory. `/home/$USER` is shortened to `~` |
| Branch | `  main` | Active git branch (magenta). Hidden when not in a git repo |
| 🤖 Model | `🤖 Sonnet 4.6` | The Claude model powering the session |
| 🔋 Context | `🔋 ██░░░░░░░░ 16%` | Context window usage. Color-coded: green → yellow at 70% → red at 90% |
| 💰 Cost | `💰 $0.4888` | Cumulative session cost in USD |
| ⏱ Duration | `⏱ 00:15:21` | Total wall-clock time for the session |
| ⚡ Rate limits | `⚡ 5h: 10% (🔄2h 30m)  7d: 1% (🔄5d 14h)` | Usage against rolling 5-hour and 7-day limits, with countdown to reset. Pro/Max only — hidden on free accounts |
| 📈 Stocks | `📈 AMD $142.53` | Real-time stock prices. Multiple tickers supported |

## Enabling and disabling sections

Each section can be toggled independently at the top of `statusline.sh`:

```bash
SHOW_CWD=true
SHOW_MODEL=true
SHOW_CONTEXT=true
SHOW_COST=true
SHOW_DURATION=false    # ← disabled
SHOW_RATE_LIMITS=true
SHOW_STOCK=true
```

Set any to `false` to remove it from the bar entirely.

## Changing emojis

Every emoji is defined alongside its toggle on the same line:

```bash
SHOW_CWD=true          ; EMOJI_CWD="📁"
SHOW_MODEL=true        ; EMOJI_MODEL="🤖"
SHOW_CONTEXT=true      ; EMOJI_CONTEXT="🔋"
SHOW_COST=true         ; EMOJI_COST="💰"
SHOW_DURATION=true     ; EMOJI_DURATION="⏱"
SHOW_RATE_LIMITS=true  ; EMOJI_RATE="⚡"  ; EMOJI_RESET="🔄"
SHOW_STOCK=true        ; EMOJI_STOCK="📈"
```

Change any emoji and it updates everywhere that section uses it.

## Managing stock tickers

Stocks are controlled via `~/.claude_statusline.json` — **not** inside the script. Add or remove tickers by editing this file:

```json
{
  "stocks": {
    "AMD":  { "price": null, "last_updated": 0 },
    "NVDA": { "price": null, "last_updated": 0 },
    "TSLA": { "price": null, "last_updated": 0 }
  }
}
```

- **Add a ticker** — add an entry with `"price": null, "last_updated": 0`
- **Remove a ticker** — delete its entry
- The script writes `price` and `last_updated` automatically on each successful fetch

### Stock refresh behavior

| Situation | Display |
|---|---|
| Price fresh (< 5 min old) | `📈 AMD $142.53` |
| Price stale (> 1 hour, fetch still failing) | `📈 AMD $142.53 (⚠️ 2h 10m ago)` |
| No price ever fetched and API unreachable | section silently hidden |

Thresholds are configurable in `statusline.sh`:

```bash
STOCK_REFRESH_TTL=300   # how often to attempt a refresh (seconds)
STOCK_STALE_TTL=3600    # how long before the ⚠️ warning appears (seconds)
```

---

## Technical reference

### Files

| File | Purpose |
|---|---|
| `~/repos/dotfiles/.claude/statusline.sh` | The script — version-controlled source |
| `~/.claude/statusline.sh` | Symlink pointing to the source above |
| `~/.claude/settings.json` | Contains the `statusLine` config block |
| `~/.claude_statusline.json` | Stock tickers and cached prices — user-controlled |

The script lives in the dotfiles repo for version control. A symlink makes it available where Claude Code expects it:

```bash
ln -s $HOME/repos/dotfiles/.claude/statusline.sh $HOME/.claude/statusline.sh
```

### settings.json config

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

Optional extra fields:
- `"padding": 2` — extra horizontal spacing
- `"refreshInterval": 1` — re-run every N seconds even when idle (makes the duration tick in real-time)

### Required tools

| Tool | Install |
|---|---|
| `jq` | `sudo apt install jq` |
| `curl` | `sudo apt install curl` |

If any tool is missing the bar prints an error instead of the normal output:
```
Status bar error: missing tools: jq — install them to enable the status bar
```

### How it works

Claude Code runs `statusline.sh` after each assistant message, passing a JSON blob via **stdin**. Whatever the script prints to stdout becomes the status bar.

The script is structured in five sections:

```
statusline.sh
├── CONFIGURATION   toggle flags, emojis, stock settings
├── REQUIRED TOOLS  dependency check
├── COLORS          ANSI escape codes ($'...' syntax — real ESC bytes)
├── HELPERS         pick_color, render_bar, format_countdown
├── SECTIONS        one function per status item
└── ASSEMBLE        read stdin, call enabled sections, join & print
```

Each `section_*` function reads from the global `$input` variable and echoes a fully-formatted string. The assembly block joins all non-empty results with a double-space separator.

### Color variables

Colors use `$'...'` syntax so they contain real ESC bytes and can be safely embedded anywhere — in variables, function outputs, or `echo`:

```bash
RESET=$'\033[0m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
CYAN=$'\033[36m'      # CWD
MAGENTA=$'\033[35m'   # git branch
GREEN=$'\033[32m'     # low usage
YELLOW=$'\033[33m'    # medium usage / cost / stock price
RED=$'\033[31m'       # high usage
```

### Full JSON schema (stdin input)

```json
{
  "session_id": "...",
  "transcript_path": "/home/jcarranz/.claude/projects/.../session.jsonl",
  "cwd": "/home/jcarranz/repos/dotfiles",
  "model": {
    "id": "claude-sonnet-4-6",
    "display_name": "Sonnet 4.6"
  },
  "version": "2.1.101",
  "cost": {
    "total_cost_usd": 0.488,
    "total_duration_ms": 921181,
    "total_api_duration_ms": 183094,
    "total_lines_added": 75,
    "total_lines_removed": 31
  },
  "context_window": {
    "total_input_tokens": 6235,
    "total_output_tokens": 12379,
    "context_window_size": 200000,
    "current_usage": {
      "input_tokens": 3,
      "output_tokens": 59,
      "cache_creation_input_tokens": 75,
      "cache_read_input_tokens": 32589
    },
    "used_percentage": 16,
    "remaining_percentage": 84
  },
  "exceeds_200k_tokens": false,
  "rate_limits": {
    "five_hour": {
      "used_percentage": 10,
      "resets_at": 1775934000
    },
    "seven_day": {
      "used_percentage": 1,
      "resets_at": 1776520800
    }
  }
}
```

### Available fields reference

#### Model
- `.model.display_name` — e.g. `"Sonnet 4.6"`
- `.model.id` — e.g. `"claude-sonnet-4-6"`

#### Cost & time
- `.cost.total_cost_usd` — session cost in USD
- `.cost.total_duration_ms` — total wall-clock time (ms)
- `.cost.total_api_duration_ms` — time spent waiting for API (ms)
- `.cost.total_lines_added` / `.cost.total_lines_removed` — code edits this session

#### Context window
- `.context_window.used_percentage` — 0–100
- `.context_window.remaining_percentage` — 0–100
- `.context_window.context_window_size` — max tokens (200000 default)
- `.context_window.total_input_tokens` — cumulative input tokens
- `.context_window.total_output_tokens` — cumulative output tokens
- `.context_window.current_usage.cache_read_input_tokens` — tokens served from cache

#### Rate limits (Pro/Max only)
- `.rate_limits.five_hour.used_percentage`
- `.rate_limits.five_hour.resets_at` — Unix epoch seconds
- `.rate_limits.seven_day.used_percentage`
- `.rate_limits.seven_day.resets_at` — Unix epoch seconds

#### Other
- `.cwd` — current working directory
- `.version` — Claude Code version
- `.transcript_path` — path to the session JSONL file

### Debugging

To inspect the raw JSON Claude Code sends to the script, temporarily add this line after `input=$(cat)`:

```bash
echo "$input" > /tmp/statusline_debug.json
```

Then after any message: `cat /tmp/statusline_debug.json | jq .`

### Adding a new section

1. Add a toggle + emoji to the CONFIGURATION block:
   ```bash
   SHOW_MYITEM=true ; EMOJI_MYITEM="🔧"
   ```
2. Write a `section_myitem()` function in the SECTIONS block that echoes a formatted string (or nothing if data is unavailable)
3. Add it to the ASSEMBLE block:
   ```bash
   $SHOW_MYITEM && { s=$(section_myitem); [ -n "$s" ] && parts+=("$s"); }
   ```
