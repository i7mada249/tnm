#!/usr/bin/env python3
"""
Interactive shell for tnm — shows groups, allows add/delete, and lists main commands.
"""
import sys
import subprocess
from pathlib import Path
import os


# --- Color helpers -------------------------------------------------
# Respect NO_COLOR or TERM-less environments
def _supports_color():
    if os.environ.get('NO_COLOR'):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

_COLOR_ON = _supports_color()

_COLORS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'bright_black': 90,
    'bright_red': 91,
    'bright_green': 92,
    'bright_yellow': 93,
    'bright_blue': 94,
    'bright_magenta': 95,
    'bright_cyan': 96,
    'bright_white': 97,
}


def c(text, color=None, bold=False):
    """Colorize text using ANSI SGR codes when supported."""
    if not _COLOR_ON or not color:
        return text
    code = _COLORS.get(color, None)
    if code is None:
        return text
    parts = []
    if bold:
        parts.append('1')
    parts.append(str(code))
    return f"\033[{';'.join(parts)}m{text}\033[0m"

# -------------------------------------------------------------------

try:
    # Import management helpers from tnm.py
    from tnm import load_groups, save_groups, create_group
except Exception:
    # If import fails, provide minimal fallback implementations
    import os, json

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


ASCII = r'''
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░████████╗███╗░░██╗███╗░░░███╗░░░░
░░░╚══██╔══╝████╗░██║████╗░████║░░░░
░░░░░░██║░░░██╔██╗██║██╔████╔██║░░░░
░░░░░░██║░░░██║╚████║██║╚██╔╝██║░░░░
░░░░░░██║░░░██║░╚███║██║░╚═╝░██║░░░░
░░░░░░╚═╝░░░╚═╝░░╚══╝╚═╝░░░░░╚═╝░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░  Terminal Notes Manager ░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
'''


def clear():
    print('\033c', end='')


def pause():
    input('\nPress Enter to continue...')


def list_groups():
    groups = load_groups()
    if not groups:
        print(c('No groups defined yet.', 'bright_red'))
        return
    print(c('Defined groups:', 'bright_green', bold=True))
    for name, path in sorted(groups.items()):
        print(f"  - {c(name, 'bright_yellow')} : {c(path, 'bright_blue')}")


def add_group_interactive():
    name = input(c('New group name: ', 'magenta', bold=True)).strip()
    if not name:
        print(c('Cancelled — empty name.', 'red'))
        return
    path = input(c('Path to markdown file (leave blank for default ~/tnm/<name>.md): ', 'cyan')).strip()
    if not path:
        path = f"~/tnm/{name}.md"
        print(c(f"Using default path: {path}", 'bright_black'))
    groups = load_groups()
    if name in groups:
        resp = input(f"Group '{name}' exists. Overwrite mapping? [y/N]: ").strip().lower()
        if resp not in ('y', 'yes'):
            print('Cancelled.')
            return
    ok = create_group(name, path, overwrite=True)
    if ok:
        print(c(f"Group '{name}' -> {path} saved.", 'bright_green'))
    else:
        print(c('Failed to save group configuration.', 'red'))


def delete_group_interactive():
    name = input(c('Group name to delete: ', 'magenta', bold=True)).strip()
    if not name:
        print(c('Cancelled — empty name.', 'red'))
        return
    groups = load_groups()
    if name not in groups:
        print(f"Group '{name}' not found.")
        return
    resp = input(c(f"Delete group '{name}' (will not delete the file) ? [y/N]: ", 'yellow')).strip().lower()
    if resp not in ('y', 'yes'):
        print(c('Cancelled.', 'red'))
        return
    groups.pop(name, None)
    if save_groups(groups):
        print(c(f"Group '{name}' removed.", 'bright_green'))
    else:
        print(c('Failed to update groups file.', 'red'))


def show_help():
    print(c('Main commands:', 'bright_blue', bold=True))
    print(c('  -n NAME PATH   Create a new group mapping (tnm -n NAME PATH)', 'bright_white'))
    print(c('  -g NAME        Add last command to group (tnm -g NAME)', 'bright_white'))
    print(c('  -l             List groups (tnm -l)', 'bright_white'))
    print(c('  --dry-run      Show what would be written (tnm --dry-run)', 'bright_white'))
    print(c('  -y             Skip confirmations where applicable', 'bright_white'))


def show_history_interactive():
    """Show last 10 saved entries for a chosen group and optionally view full entry."""
    groups = load_groups()
    if not groups:
        print('No groups defined yet.')
        return
    print(c('Choose a group to view history:', 'bright_blue', bold=True))
    names = sorted(groups.keys())
    for i, name in enumerate(names, 1):
        print(f"  {c(str(i)+'.', 'bright_green')} {c(name, 'bright_yellow')} -> {c(groups[name], 'bright_blue')}")
    try:
        sel = input('\nEnter number (or blank to cancel): ').strip()
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.')
        return
    if not sel:
        return
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(names):
            print('Invalid selection.')
            return
    except ValueError:
        print('Invalid input.')
        return
    name = names[idx]
    path = groups[name]
    p = Path(path).expanduser()
    if not p.exists():
        print(c(f"History file '{p}' does not exist or has no entries.", 'red'))
        return
    try:
        text = p.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Failed to read {p}: {e}")
        return
    # split entries by separator used in tnm (\n---\n)
    parts = [part.strip() for part in text.split('\n---\n') if part.strip()]
    if not parts:
        print('No entries found in the file.')
        return
    # show last 10 (newest last in file, so take last parts)
    recent = parts[-10:]
    # display with newest first
    recent = list(reversed(recent))
    print(c(f"\nLast {len(recent)} entries for group '{name}':\n", 'bright_green', bold=True))
    for i, entry in enumerate(recent, 1):
        # title is first non-empty line
        title = '(no title)'
        for line in entry.splitlines():
            l = line.strip()
            if l:
                title = l
                break
        # try to extract metadata line (second non-empty)
        meta = ''
        lines = [ln for ln in entry.splitlines() if ln.strip()]
        if len(lines) >= 2:
            meta = lines[1]
    print(f"  {c(str(i)+'.', 'bright_green')} {c(title, 'bright_yellow')} {c(meta, 'bright_black')}")

    while True:
        choice = input('\nEnter entry number to view (or blank to return): ').strip()
        if not choice:
            return
        try:
            ci = int(choice) - 1
            if ci < 0 or ci >= len(recent):
                print('Invalid number')
                continue
        except ValueError:
            print('Invalid input')
            continue
    print('\n' + c('=' * 40, 'bright_black') + '\n')
    print(c(recent[ci], 'bright_white'))
    print('\n' + c('=' * 40, 'bright_black') + '\n')
    input(c('Press Enter to continue...', 'bright_blue'))


def uninstall_interactive():
    """Run the uninstall script (if present) after user confirmation."""
    script_dir = Path(__file__).resolve().parent
    uninstall_script = script_dir / 'uninstall_tnm.sh'
    print(c('This will uninstall tnm from the default user locations:', 'yellow'))
    print(c('  - ~/.local/share/tnm (installed files)', 'bright_black'))
    print(c('  - ~/.local/bin/tnm (launcher)', 'bright_black'))
    print(c('  - ~/.config/tnm (groups config)', 'bright_black'))
    resp = input(c('Are you sure you want to continue? [y/N]: ', 'yellow')).strip().lower()
    if resp not in ('y', 'yes'):
        print(c('Cancelled.', 'red'))
        return
    if uninstall_script.exists():
        try:
            print(c(f'Running uninstall script: {uninstall_script}', 'bright_blue'))
            subprocess.run(['bash', str(uninstall_script)], check=True)
            print(c('Uninstall script completed.', 'bright_green'))
        except subprocess.CalledProcessError as e:
            print(f'Uninstall script failed: {e}')
    else:
        # fallback: perform removal directly
        print(c('Uninstall script not found in install dir; performing default removal now...', 'yellow'))
        try:
            subprocess.run(['rm', '-rf', str(Path.home() / '.local' / 'share' / 'tnm')], check=False)
            subprocess.run(['rm', '-f', str(Path.home() / '.local' / 'bin' / 'tnm')], check=False)
            subprocess.run(['rm', '-rf', str(Path.home() / '.config' / 'tnm')], check=False)
            print(c('Default uninstall actions completed.', 'bright_green'))
        except Exception as e:
            print(f'Failed to remove files: {e}')


def update_interactive():
    """Run the update script from the installed share dir (or attempt to download it)"""
    script_dir = Path(__file__).resolve().parent
    update_script = script_dir / 'update_tnm.sh'
    print(c('This will fetch the latest tnm files from https://github.com/i7mada249/tnm and update the installed scripts.', 'yellow'))
    resp = input(c('Continue and update? [y/N]: ', 'yellow')).strip().lower()
    if resp not in ('y', 'yes'):
        print('Cancelled.')
        return

    if update_script.exists():
        try:
            print(c(f'Running update script: {update_script}', 'bright_blue'))
            subprocess.run(['bash', str(update_script)], check=True)
            print(c('Update completed.', 'bright_green'))
        except subprocess.CalledProcessError as e:
            print(f'Update script failed: {e}')
    else:
        # fallback: try to download update_tnm.sh from GitHub raw and run it
        url = 'https://raw.githubusercontent.com/i7mada249/tnm/main/update_tnm.sh'
        try:
            import urllib.request
            print(c(f'Downloading update script from {url}...', 'bright_blue'))
            data = urllib.request.urlopen(url, timeout=15).read()
            tmp = script_dir / 'update_tnm_downloaded.sh'
            tmp.write_bytes(data)
            tmp.chmod(0o755)
            subprocess.run(['bash', str(tmp)], check=True)
            tmp.unlink()
            print(c('Update completed (downloaded script).', 'bright_green'))
        except Exception as e:
            print(f'Failed to download/run update script: {e}')


def main_loop():
    while True:
        clear()
        print(c(ASCII, 'cyan'))
        list_groups()
        print('\n' + c('Options:', 'bright_blue', bold=True))
        print(f"  {c('[a]', 'green')} {c('Add group', 'bright_white')}")
        print(f"  {c('[d]', 'green')} {c('Delete group', 'bright_white')}")
        print(f"  {c('[l]', 'green')} {c('List groups', 'bright_white')}")
        print(f"  {c('[v]', 'green')} {c('View group history', 'bright_white')}")
        print(f"  {c('[r]', 'green')} {c('Update tnm from repo', 'bright_white')}")
        print(f"  {c('[u]', 'green')} {c('Uninstall tnm', 'bright_white')}")
        print(f"  {c('[h]', 'green')} {c('Help (show main commands)', 'bright_white')}")
        print(f"  {c('[q]', 'green')} {c('Quit', 'bright_white')}")
        choice = input(c('\nChoose an option: ', 'magenta', bold=True)).strip().lower()
        if choice == 'a':
            add_group_interactive()
            pause()
        elif choice == 'd':
            delete_group_interactive()
            pause()
        elif choice == 'l':
            clear()
            list_groups()
            pause()
        elif choice == 'v':
            clear()
            show_history_interactive()
            pause()
        elif choice == 'r':
            clear()
            update_interactive()
            pause()
        elif choice == 'u':
            clear()
            uninstall_interactive()
            pause()
        elif choice == 'h':
            clear()
            show_help()
            pause()
        elif choice == 'q':
            print('Goodbye.')
            return
        else:
            print('Unknown option.')
            pause()


if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print('\nExiting.')
