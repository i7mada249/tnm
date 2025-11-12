#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path


def get_last_command():
    """Return the last command from an interactive shell.

    Tries the user's login shell with `fc -ln -1`. If that fails, falls
    back to reading a likely history file (HISTFILE, ~/.bash_history or
    ~/.zsh_history) and returns the last non-empty line.
    Returns None on failure.
    """
    shell = os.environ.get('SHELL', 'bash')
    try:
        last = subprocess.check_output([shell, '-i', '-c', 'fc -ln -1'], text=True, stderr=subprocess.DEVNULL)
        last = last.strip()
        if last:
            return last
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: try HISTFILE or common history files
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
                    if not l:
                        continue
                    # zsh history lines may have timestamp prefixes like ': 160000:0;cmd'
                    if l.startswith(':') and ';' in l:
                        l = l.split(';', 1)[1]
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
    groups[name] = os.path.expanduser(path)
    return save_groups(groups)


def get_group_path(name: str):
    groups = load_groups()
    return groups.get(name)


def usage_and_exit(msg: str = None, code: int = 1):
    if msg:
        print(msg)
    print("\nUsage:\n  Create group: tnm -n NAME PATH\n  Add to group: tnm -g NAME [-y] [--dry-run]\n  List groups: tnm -l\n")
    sys.exit(code)


def main(argv=None):
    # raw argv parsing to support the -NAME style command
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        usage_and_exit()

    # collect global flags
    dry_run = '--dry-run' in argv
    yes = '-y' in argv or '--yes' in argv

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
        if len(argv) < 3:
            usage_and_exit('Error: missing NAME or PATH for new group')
        name = argv[1]
        path = argv[2]
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
            groups = load_groups()
            if groups:
                print(f"Group '{name}' not found. Available groups: {', '.join(sorted(groups.keys()))}")
            else:
                print("No groups defined yet. Create one with: tnm -n NAME PATH")
            return

        last_cmd = get_last_command()
        if not last_cmd:
            print("Couldn't fetch the last command.")
            return

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
