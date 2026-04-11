# Claude Code Status Bar Guide

A customizable status bar at the bottom of Claude Code that displays real-time session info.

## Files

| File | Purpose |
|---|---|
| `~/repos/dotfiles/.claude/statusline.sh` | The script (version-controlled source) |
| `~/.claude/statusline.sh` | Symlink pointing to the source above |
| `~/.claude/settings.json` | Contains the `statusLine` config block |

The script lives in the dotfiles repo for version control. A symlink makes it available where Claude Code expects it:

```bash
ln -s $HOME/repos/dotfiles/.claude/statusline.sh $HOME/.claude/statusline.sh
```

## Required tools

The script depends on the following tools. If any are missing, the status bar will display an error message instead of the normal output:

| Tool | Install |
|---|---|
| `jq` | `sudo apt install jq` |

The script checks for missing tools at startup and prints:
```
Status bar error: missing tools: jq — install them to enable the status bar
```

To add more required tools, edit the `REQUIRED_TOOLS` array at the top of `statusline.sh`:
```bash
REQUIRED_TOOLS=("jq" "git")
```

## How it works

Claude Code runs the script after each assistant message, passing a JSON blob via **stdin**. Whatever the script prints to stdout becomes the status bar.

## Current bar output

```
📁 ~/repos/dotfiles  main  🤖 Sonnet 4.6  🔋 ██░░░░░░░░ 16%  💰 $0.4888  ⏱ 00:15:21  ⚡ 5h: 10% (↺14:00)  7d: 1% (↺Sun Apr 20)
```

- **📁 CWD** — cyan, bold. Shows `~` instead of `/home/$USER`
- **branch** — magenta. Only shown when inside a git repo. Hidden otherwise.
- **🤖 Model** — dimmed
- **🔋 Context bar** — color-coded: green (0–69%), yellow (70–89%), red (90%+). Uses `█`/`░` block characters.
- **💰 Cost** — yellow, 4 decimal places
- **⏱ Duration** — total wall-clock time for the session
- **⚡ Rate limits** — only shown on Pro/Max accounts. Color-coded: green (0–69%), yellow (70–89%), red (90%+).
  - `5h` — 5-hour rolling window usage. `↺HH:MM` shows the local time it resets.
  - `7d` — 7-day rolling window usage. `↺Day Mon DD` shows the date it resets.

## Colors reference

```bash
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[36m'      # CWD
MAGENTA='\033[35m'   # git branch
GREEN='\033[32m'     # context bar low usage
YELLOW='\033[33m'    # context bar medium / cost
RED='\033[31m'       # context bar high usage
```

## Current settings.json config

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
- `"refreshInterval": 1` — re-run every N seconds even when idle (makes duration tick in real-time)

## Full JSON schema (stdin input)

```json
{
  "session_id": "...",
  "transcript_path": "/home/jcarranz/.claude/projects/.../session.jsonl",
  "cwd": "/home/jcarranz/repos/dotfiles",
  "model": {
    "id": "claude-sonnet-4-6",
    "display_name": "Sonnet 4.6"
  },
  "workspace": {
    "current_dir": "/home/jcarranz/repos/dotfiles",
    "project_dir": "/home/jcarranz/repos/dotfiles",
    "added_dirs": []
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

## Available fields reference

### Model
- `.model.display_name` — e.g. `"Sonnet 4.6"`
- `.model.id` — e.g. `"claude-sonnet-4-6"`

### Cost & time
- `.cost.total_cost_usd` — session cost in USD
- `.cost.total_duration_ms` — total wall-clock time (ms)
- `.cost.total_api_duration_ms` — time spent waiting for API (ms)
- `.cost.total_lines_added` / `.cost.total_lines_removed` — code edits

### Context window
- `.context_window.used_percentage` — 0–100
- `.context_window.remaining_percentage` — 0–100
- `.context_window.context_window_size` — max tokens (200000 default)
- `.context_window.total_input_tokens` — cumulative input tokens
- `.context_window.total_output_tokens` — cumulative output tokens
- `.context_window.current_usage.cache_read_input_tokens` — tokens read from cache

### Rate limits (Pro/Max)
- `.rate_limits.five_hour.used_percentage`
- `.rate_limits.seven_day.used_percentage`
- `.rate_limits.five_hour.resets_at` — Unix epoch seconds

### Other
- `.cwd` — current working directory
- `.version` — Claude Code version
- `.transcript_path` — path to session JSONL file

## Debugging

To inspect the raw JSON Claude Code sends to the script, temporarily add this line after `input=$(cat)`:

```bash
echo "$input" > /tmp/statusline_debug.json
```

Then after any message run: `cat /tmp/statusline_debug.json | jq .`

## Common customizations

### Add rate limit display
```bash
five_h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // 0')
printf '... | 5h limit: %s%%' "$five_h"
```

### Make duration tick in real-time
Add `"refreshInterval": 1` to the `statusLine` block in `~/.claude/settings.json`.
