# Glint MVP Design

**Date**: 2026-03-16  
**Status**: Approved  
**Scope**: MVP — turn-level folding with prompt navigation

---

## Problem

When using Claude Code / OpenCode, the AI outputs hundreds of lines per turn. Users have to manually scroll to find what changed, whether there were errors, and where the next prompt starts. The terminal's linear output model doesn't match how agent-driven work actually flows.

---

## Solution

Glint is a PTY wrapper that captures AI agent output in real-time and renders it as a navigable list of **turns** (prompt → response pairs). Each turn is collapsible to a single line. Users navigate turns with `j/k`, expand with `Enter`.

This is a **reading layer only** — no AI API, no code editing, no git UI.

---

## Architecture

```
glint -- claude        # or: glint -- opencode
```

```
┌─────────────────────────────────────────┐
│               Glint Process             │
│                                         │
│  ┌─────────────┐    ┌────────────────┐  │
│  │ PTY Manager │───▶│  Turn Parser   │  │
│  │ (ptyprocess)│    │                │  │
│  └─────────────┘    └───────┬────────┘  │
│        ▲                    │ Turn      │
│   stdin│                    ▼ objects   │
│  ┌─────┴──────────────────────────────┐ │
│  │         Textual TUI App            │ │
│  │   TurnWidget × N  (folded list)    │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
         │ fork/exec
         ▼
    claude / opencode
```

### Fold Unit: The Turn

A **turn** is the atomic unit of navigation:

```
[Turn N]
  prompt:   <what the user typed>
  response: <everything the AI output until the next prompt>
```

Collapsed view: `▶ Turn 3 — fix the auth bug in login.py`  
Expanded view: full raw output of that turn, rendered with ANSI colors.

---

## Components

### `pty_manager.py`
- Spawns the child process (`claude`, `opencode`, or any command) in a pseudo-terminal via `ptyprocess`
- Reads stdout/stderr asynchronously, writes to Turn Parser
- Passes stdin keystrokes through to child process (except Glint hotkeys)

### `turn_parser.py`
- Maintains a buffer of incoming bytes
- Detects **turn boundaries**: a new turn starts when the user submits input (Enter keypress is detected on stdin path)
- Emits `Turn` objects: `{id, prompt_text, response_bytes, is_complete}`
- Streams partial response bytes to the active turn as they arrive

### `app.py` (Textual App)
- Main TUI application
- Layout: full-screen turn list + bottom input bar
- Receives `Turn` objects via Textual message queue (thread-safe)
- Manages focus and keyboard navigation

### `widgets/turn_widget.py`
- Displays one turn in collapsed or expanded state
- **Collapsed**: `▶ Turn N — [first line of response, truncated to 60 chars]`
- **Expanded**: full response rendered with ANSI escape sequences

---

## Turn Boundary Detection

**Boundary signal**: stdin Enter keypress (`\r` or `\n`) captured before forwarding to child process.

1. User types in Glint's input bar → Glint captures the text as `prompt_text`
2. User hits Enter → Glint records boundary, opens new Turn, forwards keystroke to PTY
3. PTY output accumulates into the current Turn's `response_bytes`
4. Next Enter from user → closes current Turn, opens new one

**Edge cases**:
- Multi-line input (Shift+Enter): accumulate, boundary only on plain Enter
- Child process exits: flush final turn as complete
- Initial output before first prompt: captured as Turn 0 with empty prompt (startup messages)

---

## TUI Layout

```
┌──────────────────────────────────────────┐
│ glint  claude  00:03:42                  │
├──────────────────────────────────────────┤
│ ▶ Turn 1 — 帮我实现用户登录功能           │  ← collapsed
│ ▶ Turn 2 — 写个测试                      │  ← collapsed
│ ▼ Turn 3 — fix the auth bug             │  ← expanded (focused)
│   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄   │
│   I'll fix the bug in src/auth.py...    │
│   ```python                             │
│   def login(user, pw):                  │
│       ...                               │
│   ```                                   │
│   Running pytest... 3 passed ✓          │
│   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄   │
│ ▶ Turn 4 — 再加个 rate limit            │  ← collapsed
├──────────────────────────────────────────┤
│ > █                                      │
└──────────────────────────────────────────┘
```

### Keybindings

| Key | Action |
|-----|--------|
| `j` / `↓` | Focus next turn |
| `k` / `↑` | Focus previous turn |
| `Enter` | Toggle expand / collapse focused turn |
| `G` | Jump to latest turn (bottom) |
| `g` | Jump to first turn (top) |
| `` ` `` | Toggle raw PTY view (escape hatch — shows unprocessed output) |
| `q` | Quit Glint (terminates child process) |

---

## Technology

- **Language**: Python 3.11+
- **TUI Framework**: [Textual](https://textual.textualize.io/)
- **PTY**: `ptyprocess` library
- **ANSI rendering**: Textual's built-in `RichLog` or `Static` with `markup=False, highlight=False`
- **Packaging**: `pyproject.toml` + `uv`, installable via `pip install glint-tui`

---

## MVP Scope

### In scope
- PTY wrapper launching any command (`glint -- <cmd>`)
- Turn-level folding (prompt + full response = one fold unit)
- j/k/Enter navigation
- Raw view escape hatch (`` ` `` key)
- ANSI color preservation in expanded view
- Works with `claude` and `opencode`

### Explicitly out of scope (future versions)
- Within-response semantic block classification (SPEECH / WRITE_FILE / RUN_COMMAND / OUTPUT)
- Post-turn summary cards (files changed, error count)
- Error surfacing / real-time highlighting
- Prompt sidebar with labels
- Session persistence / export to markdown
- Search within session

---

## Success Criteria

1. `glint -- claude` launches Claude Code inside Glint with no visible behavior change
2. Each submitted prompt creates a new turn entry in the list
3. Turns are collapsed by default; `Enter` expands to full output
4. `j/k` navigation moves focus between turns
5. `` ` `` shows the raw PTY stream
6. ANSI colors are preserved in expanded view
7. No input lag vs. running `claude` directly (< 5ms additional latency)
