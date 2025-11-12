#!/usr/bin/env bash
set -euo pipefail

# uninstall_tnm.sh
# Remove files installed by install.sh

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      FORCE=1; shift;;
    -h|--help)
      echo "Usage: $0 [--force]"; exit 0;;
    *)
      echo "Unknown arg: $1"; exit 1;;
  esac
done

SHARE_DIR="$HOME/.local/share/tnm"
BIN_LAUNCHER="$HOME/.local/bin/tnm"
CONFIG_DIR="$HOME/.config/tnm"

echo "This will remove the following (if present):"
echo "  $SHARE_DIR"
echo "  $BIN_LAUNCHER"
echo "  $CONFIG_DIR"

if [[ $FORCE -ne 1 ]]; then
  read -p "Continue and delete these files? [y/N]: " ans
  [[ "$ans" =~ ^[Yy] ]] || { echo "Aborted."; exit 0; }
fi

rm -rf "$SHARE_DIR" || true
rm -f "$BIN_LAUNCHER" || true
rm -rf "$CONFIG_DIR" || true

echo "Uninstalled tnm (removed files above)."
