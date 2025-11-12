# tnm — Terminal Notes Manager

A small CLI helper to capture your last interactive shell command and save it as a nicely formatted Markdown entry. Useful for keeping quick notes about commands, workflows, or snippets grouped by topic.

## Overview

- Capture the last command you ran in an interactive shell (uses your `$SHELL` or falls back to common history files).
- Save the command + a user-provided title and description into a Markdown file.
- Support named "groups" (each group maps to a Markdown file) so you can collect related commands together (for example: `nano` edits, git snippets, docker commands, etc.).
- Persist group definitions in `$XDG_CONFIG_HOME/tnm/groups.json` (or `~/.config/tnm/groups.json`).

## Installing

Just keep the `tnm.py` script somewhere on your PATH and make it executable:

```bash
# from the repository root
chmod +x tnm.py
# optionally move it to ~/.local/bin or /usr/local/bin
mv tnm.py ~/.local/bin/tnm
```

(Or run it directly with your Python interpreter: `python /path/to/tnm.py ...`)

## Usage

Create a new group (name -> markdown file):

```bash
tnm -n NAME PATH
# example
tnm -n nano ~/Documents/nano_commands.md
```

List defined groups:

```bash
tnm -l
```

Add the last command to a group:

```bash
tnm -g NAME
# example
tnm -g nano
```

You will be prompted for a Title and Description for the saved entry (unless you script input). By default the tool appends the entry automatically. Use `--dry-run` to print the resulting entry instead of writing it.

Global flags

- `-n NAME PATH` or `--new NAME PATH` — create (or overwrite) a named group
- `-g NAME` or `--group NAME` — add the last command to the named group file
- `-l` or `--list` — list configured groups
- `--dry-run` — show the entry that would be written
- `-y` or `--yes` — (where applicable) skip interactive confirmations


# tnm — Terminal Notes Manager

Terminal Notes Manager (tnm) is a small command-line helper to capture the last command you ran in an interactive shell, add a short title/description, and save it as a nicely formatted Markdown entry. Commands are grouped into named "groups" (each group maps to a Markdown file) so you can collect related snippets together.

This repository includes:

- `tnm.py` — the CLI tool. Use it to create groups and add entries from the command line.
- `tnm_shell.py` — an interactive curses-free shell UI that lists groups, allows creating/deleting groups, viewing recent history, updating and uninstalling.
- `install.sh` — per-user installer that places scripts into `~/.local/share/tnm` and creates `~/.local/bin/tnm` launcher.
- `uninstall_tnm.sh` — removes installed files.
- `update_tnm.sh` — helper that updates installed files from the main GitHub repository.

Install location & config

- Installed files go to: `~/.local/share/tnm`
- Launcher: `~/.local/bin/tnm` (created by `install.sh`)
- Group definitions are stored at: `$XDG_CONFIG_HOME/tnm/groups.json` (default `~/.config/tnm/groups.json`)

Quick install (local testing)

```bash
chmod +x install.sh
./install.sh --local
export PATH="$HOME/.local/bin:$PATH"
```

Or host the repo and run the installer with `--src-base-url` pointing at the raw files.

Basic CLI usage

- Create or overwrite a group mapping:

	`tnm -n NAME [PATH]`

	If `PATH` is omitted, `tnm` will default to `/home/tnm/NAME.md`.

- List groups:

	`tnm -l`

- Add the last interactive shell command to a group:

	`tnm -g NAME`

	This prompts for `Title` and `Description`, then appends a formatted Markdown entry to the group's file.

Global flags

- `--dry-run` — print what would be written instead of writing.
- `-y`/`--yes` — skip some confirmations.

Interactive shell (`tnm` with no args)

Run `tnm` (no args) to open the interactive shell UI. The shell provides:

- List of defined groups and their target files
- Add group (you can leave path blank; the default is `/home/tnm/<group>.md`)
- Delete group mapping (file is NOT deleted by default)
- View recent history: shows the last 10 entries for a group and lets you view full entries
- Update: fetch latest published files from https://github.com/i7mada249/tnm and replace installed scripts
- Uninstall: run the uninstall script and remove installed files

Entry format

Each saved command is appended to the group's Markdown file in this structure:

- Level-1 heading with the provided title
- A small metadata line: timestamp and cwd
- Fenced bash block with the command
- The description text
- Separator `---`

Example saved entry

```markdown
# Edit sudoers quickly

*Saved: 2025-11-12 14:05:23 — cwd: /home/me/project*

```bash
sudo EDITOR=nano visudo
```

Open visudo to edit sudoers safely.

---
```

Update and uninstall

- `update_tnm.sh` clones the repository and copies updated files into the installed folder (default `~/.local/share/tnm`). It is included by `install.sh` and callable from the interactive shell.
- `uninstall_tnm.sh` removes installed files (`~/.local/share/tnm`, `~/.local/bin/tnm`, `~/.config/tnm`) and is invoked from the interactive shell's Uninstall option.

Security and tips

- Inspect `install.sh`, `update_tnm.sh`, or any scripts before running them if you are installing from a remote source.
- The method used to capture the last command depends on your shell. `tnm` uses your `$SHELL` and `fc -ln -1` where available, and falls back to reading common history files. This may miss commands in some shell configurations.
- If you prefer non-interactive use, you can script Title/Description into `tnm -g` with input redirection or add CLI flags (future enhancement).

Examples

```bash
# create group with explicit path
tnm -n nano ~/Documents/nano_commands.md

# create group with default path (/home/tnm/git.md)
tnm -n git

# add the last command to the nano group
tnm -g nano

# list groups
tnm -l

# launch interactive shell
tnm
```

Troubleshooting

- If `tnm` is not found after install, ensure `~/.local/bin` is in your PATH and reload your shell: `export PATH="$HOME/.local/bin:$PATH"` then `hash -r` or restart the shell.

License

MIT (or choose a preferred license).
