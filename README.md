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

## Entry format

Each saved entry is appended to the group's Markdown file with this structure:

- Level-1 heading with the provided title
- A small metadata line with timestamp and current working directory
- A fenced bash block with the command
- The description text
- A horizontal rule separator

Example saved entry:

```markdown
# Edit sudoers quickly

*Saved: 2025-11-12 14:05:23 — cwd: /home/me/project*

```bash
sudo EDITOR=nano visudo
```

Open visudo to edit sudoers safely.

---
```

## Notes, caveats and tips

- The script tries to run your login shell (`$SHELL`) in interactive mode to ask it for the last command (`fc -ln -1`). This works for bash/zsh but may vary across shells and configurations.
- If `fc -ln -1` fails, `tnm` falls back to reading common history files (e.g. `~/.bash_history`, `~/.zsh_history`) and picks the last non-empty entry. That fallback may miss commands from the current interactive session depending on how your shell writes history.
- Group definitions are stored in `groups.json` under your XDG config dir. You can edit it manually if needed.
- If you want automated, non-interactive use, combine `--dry-run` and piping, or pre-fill stdin for Title/Description in a script.

## Example workflow

1. Create a group for nano-related editing snippets:

```bash
tnm -n nano ~/Documents/nano_commands.md
```

2. Run a command you want to save:

```bash
# edit a file with nano
nano ~/.config/someconfig
```

3. Save that last command into the `nano` group:

```bash
tnm -g nano
# enter Title: Edit someconfig
# enter Description: Fix path and permissions
```

## Contributing

Small improvements welcome: better history integration for other shells, optional CLI flags to provide title/description non-interactively, or additional metadata (hostname, user).

## License

MIT-style (whatever license you prefer). Update the file if you want a specific license.
