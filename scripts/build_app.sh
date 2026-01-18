#!/bin/bash
# Build MyLauncher.app
#
# Usage: ./scripts/build_app.sh
#
# Requirements:
#   - Python 3.14+ with venv activated
#   - PyInstaller: pip install pyinstaller
#   - Pillow: pip install Pillow (for icon generation)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==> Creating icon..."
python scripts/create_icon.py

echo "==> Building app with PyInstaller..."
pyinstaller MyLauncher.spec --noconfirm

echo "==> Build complete!"
echo "    App location: dist/MyLauncher.app"
echo ""
echo "To install, run:"
echo "    cp -R dist/MyLauncher.app ~/Applications/"
echo ""
echo "To run:"
echo "    open ~/Applications/MyLauncher.app"
