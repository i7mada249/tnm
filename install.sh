#!/usr/bin/env bash
set -euo pipefail

# install_tnm.sh
# Installer for tnm (Terminal Notes Manager)
# Usage:
#   ./install_tnm.sh --src-base-url <BASE_URL>
# or (install from current directory):
#   ./install_tnm.sh --local
#
# The installer will copy/download these files into ~/.local/share/tnm and
# create a launcher at ~/.local/bin/tnm.

BASE_URL=""
LOCAL=0
BIN_DIR="$HOME/.local/bin"
SHARE_DIR="$HOME/.local/share/tnm"
FORCE=0

print_usage(){
  cat <<EOF
Usage: $0 [--src-base-url BASE_URL] [--local] [--bin-dir DIR] [--share-dir DIR] [--force]

Options:
  --src-base-url BASE_URL  Base URL where raw files live (e.g. https://raw.githubusercontent.com/USER/REPO/BRANCH/path)
  --local                  Install from current working directory (expects tnm.py and tnm_shell.py present)
  --bin-dir DIR            Where to put launcher (default: ~/.local/bin)
  --share-dir DIR          Where to put script files (default: ~/.local/share/tnm)
  --force                  Overwrite existing files without prompting
  -h, --help               Show this help

Examples:
  # Install from a GitHub raw base URL
  ./install_tnm.sh --src-base-url https://raw.githubusercontent.com/you/tnm/main/

  # Install from local files in current directory
  ./install_tnm.sh --local
EOF
}

# simple arg parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --src-base-url)
      BASE_URL="$2"; shift 2;;
    --local)
      LOCAL=1; shift;;
    --bin-dir)
      BIN_DIR="$2"; shift 2;;
    --share-dir)
      SHARE_DIR="$2"; shift 2;;
    --force)
      FORCE=1; shift;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [[ $LOCAL -eq 0 && -z "$BASE_URL" ]]; then
  echo "Either --local or --src-base-url must be provided." >&2
  print_usage
  exit 1
fi

# files to install
FILES=(tnm.py tnm_shell.py README.md)

# downloader function
download_file(){
  local url="$1" dest="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$dest"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$dest" "$url"
  else
    echo "Error: neither curl nor wget is installed." >&2
    return 1
  fi
}

mkdir -p "$SHARE_DIR"
mkdir -p "$BIN_DIR"

for f in "${FILES[@]}"; do
  dest="$SHARE_DIR/$f"
  if [[ $LOCAL -eq 1 ]]; then
    if [[ ! -f "$f" ]]; then
      echo "Local file '$f' not found in current directory" >&2
      exit 1
    fi
    if [[ -f "$dest" && $FORCE -ne 1 ]]; then
      read -p "File $dest exists. Overwrite? [y/N]: " ans
      [[ "$ans" =~ ^[Yy] ]] || { echo "Skipping $f"; continue; }
    fi
    cp "$f" "$dest"
  else
    url="$BASE_URL/$f"
    tmpfile=$(mktemp)
    if ! download_file "$url" "$tmpfile"; then
      echo "Failed to download $url" >&2
      rm -f "$tmpfile"
      exit 1
    fi
    if [[ -f "$dest" && $FORCE -ne 1 ]]; then
      read -p "File $dest exists. Overwrite? [y/N]: " ans
      [[ "$ans" =~ ^[Yy] ]] || { echo "Skipping $f"; rm -f "$tmpfile"; continue; }
    fi
    mv "$tmpfile" "$dest"
  fi
  chmod +x "$dest" || true
  echo "Installed $dest"
done

# create launcher
launcher="$BIN_DIR/tnm"
if [[ -f "$launcher" && $FORCE -ne 1 ]]; then
  read -p "Launcher $launcher exists. Overwrite? [y/N]: " ans
  [[ "$ans" =~ ^[Yy] ]] || { echo "Keeping existing launcher"; exit 0; }
fi

cat > "$launcher" <<'EOF'
#!/usr/bin/env bash
SCRIPT_DIR="$HOME/.local/share/tnm"
if [ $# -eq 0 ]; then
  exec python3 "$SCRIPT_DIR/tnm_shell.py"
else
  exec python3 "$SCRIPT_DIR/tnm.py" "$@"
fi
EOF

chmod +x "$launcher"
echo "Launcher created at $launcher"

echo "\nInstallation complete. Make sure $BIN_DIR is in your PATH (e.g. add to ~/.zshrc or ~/.profile):"
echo "  export PATH=\"$BIN_DIR:\$PATH\""

echo "You can now run: tnm"