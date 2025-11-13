#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
def get_last_command():
    """Return the last command from an interactive shell.

    Attempts to ask the user's login shell for recent history and returns
    the most-recent command that doesn't look like the current tnm
    invocation. This helps avoid capturing `tnm -g ...` itself when the
    shell writes the command into history immediately.

    Falls back to reading likely history files (HISTFILE, ~/.bash_history
    or ~/.zsh_history) if needed. Returns None on failure.
    """
    shell = os.environ.get('SHELL', 'bash')
    # Build a few tokens to recognise the current invocation so we can skip it
    try:
        invoked = ' '.join(sys.argv)
        invoked_basename = Path(sys.argv[0]).name
        invoked_stem = Path(sys.argv[0]).stem
    except Exception:
        invoked = ''
        invoked_basename = ''
        invoked_stem = ''

    def looks_like_invocation(cmd: str) -> bool:
        if not cmd:
            return False
        low = cmd.strip()
        # if the command contains the script name or the full argv, treat it as invocation
        if invoked and invoked in low:
            return True
        if invoked_basename and invoked_basename in low:
            return True
        if invoked_stem and invoked_stem in low:
            return True
        return False
    histfile = os.environ.get('HISTFILE')
    candidates = []
    if histfile:
        candidates.append(histfile)
    # guess based on common shells
    if shell.endswith('zsh'):
        candidates.append(os.path.expanduser('~/.zsh_history'))
    else:
        candidates.append(os.path.expanduser('~/.bash_history'))

    for path in candidates:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as h:
                for line in reversed(h.readlines()):
                    l = line.strip()
                    if os.environ.get('TNM_DEBUG'):
                        print(f"DEBUG: file {path} line repr: {repr(line)}", file=sys.stderr)
                    if not l:
                        continue
                    # zsh history lines may have timestamp prefixes like ': 160000:0;cmd'
                    if l.startswith(':') and ';' in l:
                        l = l.split(';', 1)[1]
                    # ignore very short entries which are likely accidental keystrokes
                    if len(l.strip()) <= 1:
                        continue
                    if not looks_like_invocation(l):
                        return l
        except Exception:
            continue

    return None


def build_entry(title: str, cmd: str, desc: str) -> str:
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    cwd = os.getcwd()
    entry = []
    entry.append(f"# {title}")
    entry.append("")
    entry.append(f"*Saved: {ts} — cwd: {cwd}*")
    entry.append("")
    entry.append("```bash")
    entry.append(cmd)
    entry.append("```")
    entry.append("")
    entry.append(desc)
    entry.append("")
    entry.append("---")
    return "\n".join(entry) + "\n"


def build_session_entry(title: str, cmds: list, desc: str) -> str:
    """Build a single markdown entry that contains multiple commands from a session."""
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    cwd = os.getcwd()
    entry = []
    entry.append(f"# {title}")
    entry.append("")
    entry.append(f"*Saved: {ts} — cwd: {cwd}*")
    entry.append("")
    entry.append("Session commands:")
    entry.append("")
    entry.append("```bash")
    for c in cmds:
        entry.append(c)
    entry.append("```")
    entry.append("")
    entry.append(desc)
    entry.append("")
    entry.append("---")
    return "\n".join(entry) + "\n"


def read_history_last(n: int):
    """Read the last n commands from a likely history file.

    Best-effort: check $HISTFILE, then ~/.zsh_history, then ~/.bash_history.
    Returns a list of command strings (oldest->newest) up to n items.
    """
    shell = os.environ.get('SHELL', 'bash')
    histfile = os.environ.get('HISTFILE')
    candidates = []
    if histfile:
        candidates.append(histfile)
    if shell.endswith('zsh'):
        candidates.append(os.path.expanduser('~/.zsh_history'))
    candidates.append(os.path.expanduser('~/.bash_history'))

    for path in candidates:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as h:
                lines = [ln.strip() for ln in h.readlines() if ln.strip()]
        except Exception:
            continue

        cmds = []
        for line in reversed(lines):
            l = line
            # zsh history timestamp format: ': 160000:0;cmd'
            if l.startswith(':') and ';' in l:
                l = l.split(';', 1)[1]
            l = l.strip()
            if not l:
                continue
            # skip tnm invocations and single-char accidental entries
            if _looks_like_invocation(l):
                continue
            if len(l) <= 1:
                continue
            cmds.append(l)
            if len(cmds) >= n:
                break
        if cmds:
            return list(reversed(cmds))
    return []


def _looks_like_invocation(cmd: str) -> bool:
    """Return True if the given cmd looks like an invocation of this tnm script."""
    try:
        invoked = ' '.join(sys.argv)
        invoked_basename = Path(sys.argv[0]).name
        invoked_stem = Path(sys.argv[0]).stem
    except Exception:
        invoked = ''
        invoked_basename = ''
        invoked_stem = ''
    low = cmd.strip()
    if invoked and invoked in low:
        return True
    if invoked_basename and invoked_basename in low:
        return True
    if invoked_stem and invoked_stem in low:
        return True
    return False


CONFIG_DIR = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'tnm'
GROUPS_FILE = CONFIG_DIR / 'groups.json'


def load_groups():
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if GROUPS_FILE.exists():
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_groups(groups: dict):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, indent=2)
        return True
    except Exception:
        return False


def create_group(name: str, path: str, overwrite: bool = False) -> bool:
    groups = load_groups()
    if name in groups and not overwrite:
        return False
    target = os.path.expanduser(path)
    # create parent dir and an empty file so users see the file immediately
    try:
        tp = Path(target)
        tp.parent.mkdir(parents=True, exist_ok=True)
        if not tp.exists():
            tp.write_text('', encoding='utf-8')
    except Exception:
        # If we couldn't create the file, still save the mapping
        pass
    groups[name] = target
    return save_groups(groups)


def get_group_path(name: str):
    groups = load_groups()
    return groups.get(name)


def usage_and_exit(msg: str = None, code: int = 1):
    if msg:
        print(msg)
    usage_text = (
        "Usage:\n"
        "  Create group: tnm -n NAME [PATH]  (if PATH omitted defaults to ~/tnm/NAME.md)\n"
        "  Add to group: tnm -g NAME [-y] [--dry-run]\n"
        "  List groups: tnm -l\n"
    )
    sys.stdout.write(usage_text)
    sys.exit(code)


def main(argv=None):
    # raw argv parsing to support the -NAME style command
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        usage_and_exit()

    # collect global flags
    dry_run = '--dry-run' in argv
    yes = '-y' in argv or '--yes' in argv
    # optional command override: -c 'the command' or --cmd 'the command'
    cmd_override = None
    if '-c' in argv:
        try:
            i = argv.index('-c')
            if i + 1 < len(argv):
                cmd_override = argv[i + 1]
        except ValueError:
            pass
    if '--cmd' in argv:
        try:
            i = argv.index('--cmd')
            if i + 1 < len(argv):
                cmd_override = argv[i + 1]
        except ValueError:
            pass
    # optional: import last N commands from history as a single session entry
    last_n = None
    if '--last' in argv:
        try:
            i = argv.index('--last')
            if i + 1 < len(argv):
                last_n = int(argv[i + 1])
        except Exception:
            last_n = None

    # Quick list of groups
    if argv[0] in ('-l', '--list') or '-l' in argv:
        groups = load_groups()
        if groups:
            print('Defined groups:')
            for k, v in sorted(groups.items()):
                print(f"  {k} -> {v}")
        else:
            print('No groups defined yet. Create one with: tnm -n NAME PATH')
        return

    # Create group flow: -n NAME PATH
    if argv[0] in ('-n', '--new'):
        if len(argv) < 2:
            usage_and_exit('Error: missing NAME for new group')
        name = argv[1]
        # allow omitted PATH: default to ~/tnm/<name>.md
        if len(argv) >= 3:
            path = argv[2]
        else:
            path = os.path.join(str(Path.home()), 'tnm', f"{name}.md")
        if get_group_path(name) and not yes:
            resp = input(f"Group '{name}' already exists. Overwrite? [y/N]: ").strip().lower()
            if resp not in ('y', 'yes'):
                print('Cancelled.')
                return
        ok = create_group(name, path, overwrite=True)
        if ok:
            print(f"Group '{name}' -> {path} saved.")
        else:
            print('Failed to save group configuration.')
        return

    # Add to group flow: -g NAME
    if argv[0] in ('-g', '--group'):
        if len(argv) < 2:
            usage_and_exit('Error: missing NAME for group')
        name = argv[1]
        target = get_group_path(name)
        if not target:
            # Auto-create a default group mapping so `tnm -g NAME` is convenient
            default_path = os.path.join(str(Path.home()), 'tnm', f"{name}.md")
            created = create_group(name, default_path, overwrite=False)
            if created:
                target = default_path
                print(f"Group '{name}' not found. Created new group '{name}' -> {default_path}")
            else:
                groups = load_groups()
                if groups:
                    print(f"Group '{name}' not found. Available groups: {', '.join(sorted(groups.keys()))}")
                else:
                    print("No groups defined yet. Create one with: tnm -n NAME PATH")
                return

        # if user requested importing last N commands from history, do that
        if last_n is not None and last_n > 0:
            cmds = read_history_last(last_n)
            if not cmds:
                print("Couldn't fetch any commands from history.")
                return
            # prompt for title/desc
            try:
                title = input(f"Title for session (will contain last {last_n} commands): ").strip()
                desc = input("Description: ").strip()
            except (KeyboardInterrupt, EOFError):
                print('\nAborted by user.')
                return
            session_entry = build_session_entry(title or f'Session - last {last_n} cmds', cmds, desc or '')
            try:
                tp = Path(os.path.expanduser(target))
                tp.parent.mkdir(parents=True, exist_ok=True)
                with open(tp, 'a', encoding='utf-8') as f:
                    f.write(session_entry)
                print(f"Saved session to {tp}")
            except Exception as e:
                print(f"Failed to write to {target}: {e}")
            return

        if cmd_override:
            last_cmd = cmd_override
        else:
            last_cmd = get_last_command()
        # normalize whitespace-only results and detect non-printable-only results
        if isinstance(last_cmd, str):
            last_cmd = last_cmd.rstrip('\n')
        # compute a visible-text version to detect invisible / control-only content
        visible = ''
        if isinstance(last_cmd, str):
            visible = ''.join(ch for ch in last_cmd if ch.isprintable() and not ch.isspace())
            visible = visible.strip()
        if not last_cmd or not visible:
            # prompt the user for the command as a fallback
            try:
                fallback = input("Couldn't fetch the last command automatically. Enter command to save (or leave empty to cancel): ").strip()
            except (KeyboardInterrupt, EOFError):
                print('\nAborted by user.')
                return
            if not fallback:
                print('Cancelled.')
                return
            last_cmd = fallback
        else:
            # prefer the stripped version for display
            last_cmd = last_cmd.strip()

        print(f"Last command: {last_cmd}")
        try:
            title = input("Title: ").strip()
            desc = input("Description: ").strip()
        except (KeyboardInterrupt, EOFError):
            print('\nAborted by user.')
            return

        entry = build_entry(title or f'(no title - {name})', last_cmd, desc or '')

        if dry_run:
            print('\n--- dry-run output ---\n')
            print(entry)
            return

        try:
            tp = Path(os.path.expanduser(target))
            tp.parent.mkdir(parents=True, exist_ok=True)
            with open(tp, 'a', encoding='utf-8') as f:
                f.write(entry)
            print(f"Saved to {tp}")
        except Exception as e:
            print(f"Failed to write to {target}: {e}")
        return

    usage_and_exit()


if __name__ == "__main__":
    main()
