#!/usr/bin/env bash
set -euo pipefail

# update_tnm.sh
# Update installed tnm files from the main GitHub repository.
# By default it updates ~/.local/share/tnm with the latest files from the repo.

REPO="https://github.com/i7mada249/tnm.git"
INSTALL_DIR="$HOME/.local/share/tnm"
FORCE=0

print_usage(){
  cat <<EOF
Usage: $0 [--repo GIT_URL] [--install-dir PATH] [--force]

Options:
  --repo GIT_URL     Git repo to clone (default: ${REPO})
  --install-dir PATH Where to install/update files (default: ${INSTALL_DIR})
  --force            Overwrite without prompting
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"; shift 2;;
    --install-dir)
      INSTALL_DIR="$2"; shift 2;;
    --force)
      FORCE=1; shift;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

TMPDIR=$(mktemp -d)
cleanup(){ rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "Cloning $REPO to $TMPDIR (shallow)..."
if command -v git >/dev/null 2>&1; then
  git clone --depth 1 "$REPO" "$TMPDIR"
else
  echo "git not available; attempting to download tarball instead..."
  TARURL=$(echo "$REPO" | sed -e 's#https://github.com#https://codeload.github.com#' -e 's#\.git$#/tar.gz/refs/heads/main#')
  curl -fsSL "$TARURL" -o "$TMPDIR/repo.tar.gz"
  tar -xzf "$TMPDIR/repo.tar.gz" -C "$TMPDIR"
  # extracted dir will be tnm-main or similar; move up
  EXDIR=$(find "$TMPDIR" -maxdepth 1 -type d -name "*tnm*" | head -n1)
  if [[ -n "$EXDIR" ]]; then
    mv "$EXDIR"/* "$TMPDIR/"
  fi
fi

echo "Preparing to update files in: $INSTALL_DIR"
if [[ -d "$INSTALL_DIR" && $FORCE -ne 1 ]]; then
  read -p "This will overwrite files in $INSTALL_DIR. Continue? [y/N]: " ans
  [[ "$ans" =~ ^[Yy] ]] || { echo "Aborted."; exit 0; }
fi

mkdir -p "$INSTALL_DIR"

FILES=(tnm.py tnm_shell.py README.md install.sh uninstall_tnm.sh update_tnm.sh)
for f in "${FILES[@]}"; do
  src="$TMPDIR/$f"
  if [[ ! -f "$src" ]]; then
    echo "Warning: $f not found in repo, skipping"
    continue
  fi
  cp "$src" "$INSTALL_DIR/$f"
  chmod +x "$INSTALL_DIR/$f" || true
  echo "Updated $INSTALL_DIR/$f"
done

echo "Update complete. Launcher (if installed) will pick up new scripts." 
