#!/usr/bin/env python3
"""
Interactive shell for tnm — shows groups, allows add/delete, and lists main commands.
"""
import sys
import subprocess
from pathlib import Path

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
        print('No groups defined yet.')
        return
    print('Defined groups:')
    for name, path in sorted(groups.items()):
        print(f'  - {name}: {path}')


def add_group_interactive():
    name = input('New group name: ').strip()
    if not name:
        print('Cancelled — empty name.')
        return
    path = input('Path to markdown file (leave blank for default ~/tnm/<name>.md): ').strip()
    if not path:
        path = f"~/tnm/{name}.md"
        print(f"Using default path: {path}")
    groups = load_groups()
    if name in groups:
        resp = input(f"Group '{name}' exists. Overwrite mapping? [y/N]: ").strip().lower()
        if resp not in ('y', 'yes'):
            print('Cancelled.')
            return
    ok = create_group(name, path, overwrite=True)
    if ok:
        print(f"Group '{name}' -> {path} saved.")
    else:
        print('Failed to save group configuration.')


def delete_group_interactive():
    name = input('Group name to delete: ').strip()
    if not name:
        print('Cancelled — empty name.')
        return
    groups = load_groups()
    if name not in groups:
        print(f"Group '{name}' not found.")
        return
    resp = input(f"Delete group '{name}' (will not delete the file) ? [y/N]: ").strip().lower()
    if resp not in ('y', 'yes'):
        print('Cancelled.')
        return
    groups.pop(name, None)
    if save_groups(groups):
        print(f"Group '{name}' removed.")
    else:
        print('Failed to update groups file.')


def show_help():
    print('Main commands:')
    print('  -n NAME PATH   Create a new group mapping (tnm -n NAME PATH)')
    print('  -g NAME        Add last command to group (tnm -g NAME)')
    print('  -l             List groups (tnm -l)')
    print('  --dry-run      Show what would be written (tnm --dry-run)')
    print('  -y             Skip confirmations where applicable')


def show_history_interactive():
    """Show last 10 saved entries for a chosen group and optionally view full entry."""
    groups = load_groups()
    if not groups:
        print('No groups defined yet.')
        return
    print('Choose a group to view history:')
    names = sorted(groups.keys())
    for i, name in enumerate(names, 1):
        print(f'  {i}. {name} -> {groups[name]}')
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
        print(f"History file '{p}' does not exist or has no entries.")
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
    print(f"\nLast {len(recent)} entries for group '{name}':\n")
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
        print(f"  {i}. {title} {meta}")

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
        print('\n' + '=' * 40 + '\n')
        print(recent[ci])
        print('\n' + '=' * 40 + '\n')
        input('Press Enter to continue...')


def uninstall_interactive():
    """Run the uninstall script (if present) after user confirmation."""
    script_dir = Path(__file__).resolve().parent
    uninstall_script = script_dir / 'uninstall_tnm.sh'
    print('This will uninstall tnm from the default user locations:')
    print('  - ~/.local/share/tnm (installed files)')
    print('  - ~/.local/bin/tnm (launcher)')
    print('  - ~/.config/tnm (groups config)')
    resp = input('Are you sure you want to continue? [y/N]: ').strip().lower()
    if resp not in ('y', 'yes'):
        print('Cancelled.')
        return

    if uninstall_script.exists():
        try:
            print(f'Running uninstall script: {uninstall_script}')
            subprocess.run(['bash', str(uninstall_script)], check=True)
            print('Uninstall script completed.')
        except subprocess.CalledProcessError as e:
            print(f'Uninstall script failed: {e}')
    else:
        # fallback: perform removal directly
        print('Uninstall script not found in install dir; performing default removal now...')
        try:
            subprocess.run(['rm', '-rf', str(Path.home() / '.local' / 'share' / 'tnm')], check=False)
            subprocess.run(['rm', '-f', str(Path.home() / '.local' / 'bin' / 'tnm')], check=False)
            subprocess.run(['rm', '-rf', str(Path.home() / '.config' / 'tnm')], check=False)
            print('Default uninstall actions completed.')
        except Exception as e:
            print(f'Failed to remove files: {e}')


def update_interactive():
    """Run the update script from the installed share dir (or attempt to download it)"""
    script_dir = Path(__file__).resolve().parent
    update_script = script_dir / 'update_tnm.sh'
    print('This will fetch the latest tnm files from https://github.com/i7mada249/tnm and update the installed scripts.')
    resp = input('Continue and update? [y/N]: ').strip().lower()
    if resp not in ('y', 'yes'):
        print('Cancelled.')
        return

    if update_script.exists():
        try:
            print(f'Running update script: {update_script}')
            subprocess.run(['bash', str(update_script)], check=True)
            print('Update completed.')
        except subprocess.CalledProcessError as e:
            print(f'Update script failed: {e}')
    else:
        # fallback: try to download update_tnm.sh from GitHub raw and run it
        url = 'https://raw.githubusercontent.com/i7mada249/tnm/main/update_tnm.sh'
        try:
            import urllib.request
            print(f'Downloading update script from {url}...')
            data = urllib.request.urlopen(url, timeout=15).read()
            tmp = script_dir / 'update_tnm_downloaded.sh'
            tmp.write_bytes(data)
            tmp.chmod(0o755)
            subprocess.run(['bash', str(tmp)], check=True)
            tmp.unlink()
            print('Update completed (downloaded script).')
        except Exception as e:
            print(f'Failed to download/run update script: {e}')


def main_loop():
    while True:
        clear()
        print(ASCII)
        list_groups()
        print('\nOptions:')
        print('  [a] Add group')
        print('  [d] Delete group')
        print('  [l] List groups')
        print('  [v] View group history')
        print('  [r] Update tnm from repo')
        print('  [u] Uninstall tnm')
        print('  [h] Help (show main commands)')
        print('  [q] Quit')
        choice = input('\nChoose an option: ').strip().lower()
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
