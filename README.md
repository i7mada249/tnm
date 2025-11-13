# tnm — Terminal Notes Manager
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░████████╗███╗░░██╗███╗░░░███╗░░░░
░░░╚══██╔══╝████╗░██║████╗░████║░░░░
░░░░░░██║░░░██╔██╗██║██╔████╔██║░░░░
░░░░░░██║░░░██║╚████║██║╚██╔╝██║░░░░
░░░░░░██║░░░██║░╚███║██║░╚═╝░██║░░░░
░░░░░░╚═╝░░░╚═╝░░╚══╝╚═╝░░░░░╚═╝░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

Terminal Notes Manager (tnm) helps you capture commands you run in the terminal and save them as readable Markdown notes, grouped by topic. It's lightweight and intentionally simple: groups map to Markdown files, and each saved entry contains a title, timestamp, cwd, the command (fenced bash block) and an optional description.

This repo contains:

- `tnm.py` — the CLI tool
- `tnm_shell.py` — interactive terminal UI (TTY-based, no curses dependency)
- `install.sh` / `update_tnm.sh` / `uninstall_tnm.sh` — installer/update/uninstall helpers

## Table of contents

- Features
- Install
- Basic usage
- Session import (`--last`)
- Shell tips for reliable history capture
- Environment variables & debug
- Examples
- Contributing

---

## Features

- Create named groups (mapping to Markdown files)
- Append the last command to a group (with title + description)
- Bulk-import the last N commands from your current shell history as a single session entry (`--last N`)
- Interactive shell UI for browsing groups and entries
- Simple per-user installer and updater

---

## Install (per-user)

Quick locally (for testing):

```bash
chmod +x install.sh
./install.sh --local
export PATH="$HOME/.local/bin:$PATH"
```

The installer copies files to `~/.local/share/tnm` and creates a launcher at `~/.local/bin/tnm`. Group mappings live in `$XDG_CONFIG_HOME/tnm/groups.json` (defaults to `~/.config/tnm/groups.json`).

---

## Basic usage

- Create a group (map a name to a Markdown file):

```bash
tnm -n NAME [PATH]
```

If `PATH` is omitted a default path is used (for per-user installs it will be `~/tnm/<name>.md`).

- List groups:

```bash
tnm -l
```

- Add the last command to a group (prompts for title/description):

```bash
tnm -g NAME
```

- CLI flags:

- `--dry-run` — print the output instead of writing
- `-y` / `--yes` — skip confirmations
- `-c 'command'` or `--cmd 'command'` — provide the command explicitly (no auto-capture)
- `--last N` — import the last N commands from your history as a single session entry (see below)

---

## Session import: `--last N`

If you want to save multiple recent commands from the terminal you were using (without starting a special session), use `--last N`:

```bash
tnm -g work --last 20
```

This reads the last N commands from a likely history file (best-effort: `$HISTFILE`, `~/.zsh_history`, then `~/.bash_history`), filters out accidental one-character entries and tnm invocations, and appends a single Markdown session entry containing the commands to the group's file. You'll be prompted for a title and description.

Notes:

- This is best-effort: whether the last commands are present in history depends on your shell configuration (some shells append history only at exit unless configured otherwise).
- For more reliable results, see the Shell tips section below.

---

## Shell tips for reliable history capture

To make it more likely that recent commands appear in history files immediately (so `tnm` can read them), add these snippets to your shell config or run them in a terminal before working.

- **Bash** (append history on each prompt):

```bash
# add once to your ~/.bashrc or run in the session you want to record
export PROMPT_COMMAND='history -a; history -n;'
```

This forces bash to append each command to the history file as it runs and re-read new lines from the history file.

- **Zsh** (immediate history append):

```bash
# add to ~/.zshrc
setopt INC_APPEND_HISTORY
setopt SHARE_HISTORY
```

These options instruct zsh to write history incrementally so other processes (or `tnm`) can read recent commands.

---

## Environment variables & debug

- `TNM_DEBUG=1` — prints debugging information about how history was captured (helpful when diagnosing why a command wasn't found).
- `TNM_USE_SHELL_HISTORY=1` — (opt-in) allow `tnm` to spawn a non-login shell to run `fc -ln -N` (this is fragile and returns extra startup output for some shells; file-based history reading is preferred).
- Honor `NO_COLOR` for the interactive shell UI.

---

## Examples

```bash
# create group with explicit path
tnm -n nano ~/Documents/nano_commands.md

# create group with default path
tnm -n git

# add the last command to the nano group
tnm -g nano

# import the last 15 commands as one session entry
tnm -g work --last 15

# provide the command explicitly
tnm -g snippets -c "git rebase -i HEAD~3"

# launch interactive shell UI
tnm
```
