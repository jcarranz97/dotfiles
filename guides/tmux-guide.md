# 🖥️ tmux User Guide & Cheatsheet

> **Official docs:** `man tmux` → search `/copy-mode` and `/vi-copy`
> GitHub wiki: https://github.com/tmux/tmux/wiki

---

## 🧱 Core Concepts

tmux has three levels of hierarchy:

```
Session
 └── Window  (like tabs in a browser)
      └── Pane    (split panels within a window)
```

The **prefix key** (`Ctrl+b` by default) is pressed before every tmux command.

---

## 🗂️ Sessions

```bash
tmux                        # start a new session
tmux new -s work            # start a named session
tmux ls                     # list sessions
tmux attach -t work         # attach to a named session
tmux kill-session -t work   # kill a session
```

| Key              | Action                        |
|------------------|-------------------------------|
| `Ctrl+b d`       | Detach from session           |
| `Ctrl+b $`       | Rename current session        |
| `Ctrl+b s`       | List and switch sessions      |

---

## 🪟 Windows (Tabs)

| Key              | Action                        |
|------------------|-------------------------------|
| `Ctrl+b c`       | Create a new window           |
| `Ctrl+b ,`       | Rename current window         |
| `Ctrl+b n`       | Next window                   |
| `Ctrl+b p`       | Previous window               |
| `Ctrl+b 0-9`     | Switch to window by number    |
| `Ctrl+b w`       | Interactive window list       |
| `Ctrl+b &`       | Kill current window           |

---

## ✂️ Panes (Splits)

| Key              | Action                        |
|------------------|-------------------------------|
| `Ctrl+b %`       | Split vertically (side by side) |
| `Ctrl+b "`       | Split horizontally (top/bottom) |
| `Ctrl+b x`       | Kill current pane             |
| `Ctrl+b z`       | Zoom/unzoom pane (fullscreen) |
| `Ctrl+b {`       | Swap pane with the one above  |
| `Ctrl+b }`       | Swap pane with the one below  |
| `Ctrl+b Space`   | Cycle through pane layouts    |

### Pane Navigation (custom vi bindings from .tmux.conf)

These bindings are set in `~/.tmux.conf`:
```tmux
bind -r k select-pane -U   # move to pane above
bind -r j select-pane -D   # move to pane below
bind -r h select-pane -L   # move to pane left
bind -r l select-pane -R   # move to pane right
```

So after the prefix: `Ctrl+b h/j/k/l` to navigate panes like Vim.
The `-r` flag makes them **repeatable** — you can press `Ctrl+b` once then
tap `j j j` to move down three panes without re-pressing the prefix.

---

## 📋 Copy Mode (the Vim-like buffer)

Copy mode lets you scroll through terminal output and copy text.
Your `~/.tmux.conf` enables vi keys:

```tmux
set-window-option -g mode-keys vi
bind-key -T copy-mode-vi v send-keys -X begin-selection
bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel
bind-key -T copy-mode-vi V send-keys -X select-line
```

### Enter / Exit

| Key          | Action                   |
|--------------|--------------------------|
| `Ctrl+b [`   | Enter copy mode          |
| `q` / `Esc`  | Exit copy mode           |
| `Ctrl+b ]`   | Paste from tmux buffer   |

---

## 🧭 Copy Mode — Navigation

All standard vi motions work, including with **counts** (e.g. `3j`, `5w`).

### Line & Character Movement

| Key          | Action                              |
|--------------|-------------------------------------|
| `h` / `l`    | Move left / right                   |
| `j` / `k`    | Move down / up one line             |
| `3j` / `3k`  | Move down / up **3 lines**          |
| `0`          | Beginning of line                   |
| `^`          | First non-whitespace of line        |
| `$`          | End of line                         |

### Word Movement

| Key          | Action                              |
|--------------|-------------------------------------|
| `w`          | Forward one word                    |
| `5w`         | Forward **5 words**                 |
| `b`          | Back one word                       |
| `3b`         | Back **3 words**                    |
| `e`          | End of current word                 |

### Page / Buffer Movement

| Key          | Action                              |
|--------------|-------------------------------------|
| `Ctrl+f`     | Page forward (down)                 |
| `Ctrl+b`     | Page backward (up)                  |
| `Ctrl+d`     | Half-page down                      |
| `Ctrl+u`     | Half-page up                        |
| `g`          | Go to top of scrollback buffer      |
| `G`          | Go to bottom (most recent output)   |

---

## ✂️ Copy Mode — Selection & Yanking

Unlike Vim, tmux copy mode has **no operator-pending mode** — you cannot do
`y3j` in one motion. You must:
1. Start a selection
2. Extend it with motions (counts work here)
3. Yank

### Selection Modes

| Key          | Selection type                          |
|--------------|-----------------------------------------|
| `v`          | Character-wise (like Vim's `v`)         |
| `V`          | Line-wise — selects full lines          |
| `Ctrl+v`     | Rectangle/block selection               |

### Yank Workflow Examples

**Copy 3 lines downward from cursor:**
```
Ctrl+b [    # enter copy mode
V           # start line selection
3j          # extend 3 lines down (now 4 lines total are selected)
y           # yank and exit copy mode
Ctrl+b ]    # paste wherever needed
```

**Copy a word:**
```
Ctrl+b [    # enter copy mode
w           # move to the word you want
v           # start character selection
e           # extend to end of word
y           # yank
```

**Copy from cursor to end of line:**
```
Ctrl+b [    # enter copy mode
v           # start selection
$           # extend to end of line
y           # yank
```

**Copy a block of code (rectangle select):**
```
Ctrl+b [    # enter copy mode
Ctrl+v      # start block selection
3j 10l      # extend 3 lines down and 10 chars right
y           # yank the rectangle
```

---

## 🔍 Copy Mode — Search

| Key          | Action                             |
|--------------|------------------------------------|
| `/`          | Search forward in buffer           |
| `?`          | Search backward in buffer          |
| `n`          | Jump to next match                 |
| `N`          | Jump to previous match             |

```
Ctrl+b [    # enter copy mode
/error      # search for "error"
n           # next occurrence
V y         # select and yank the matching line
```

---

## 🍳 Practical Recipes

### Scroll up to read output, then return
```
Ctrl+b [    # enter copy mode
Ctrl+b      # page up through output
q           # exit, cursor returns to shell
```

### Copy the last command's output
```
Ctrl+b [    # enter copy mode
?^$         # search backward for empty line (blank line before prompt)
j           # move one line down (first line of output)
V           # start line selection
/^$         # search forward for next empty line
k           # move up to last output line
y           # yank
```

### Find and copy an error message
```
Ctrl+b [    # enter copy mode
?Error      # search backward for "Error"
V y         # select line and yank
```

---

## 📜 Scrollback Buffer

By default tmux keeps 2000 lines. To increase it in `~/.tmux.conf`:

```tmux
set -g history-limit 50000
```

---

## 📚 Useful Resources

- **Man page:** `man tmux` (authoritative reference for all commands)
- **Copy mode keys:** `man tmux` → search `/copy-mode`
- **Key table bindings:** `tmux list-keys` in your terminal
- **GitHub wiki:** https://github.com/tmux/tmux/wiki
- **tmux book (free):** https://leanpub.com/the-tao-of-tmux/read
