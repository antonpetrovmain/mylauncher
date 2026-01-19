#!/bin/bash
# MyLauncher Installer
# Downloads and installs the latest release from GitHub
set -e

APP_NAME="MyLauncher"
INSTALL_DIR="/Applications"
REPO="antonpetrovmain/mylauncher"

echo "Installing $APP_NAME..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

# Fetch latest release URL from GitHub API
echo "Fetching latest release..."
DOWNLOAD_URL=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | \
    grep "browser_download_url.*\.zip" | \
    head -1 | \
    cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not find release download URL"
    echo "Make sure there's a release at: https://github.com/$REPO/releases"
    exit 1
fi

# Download the zip
echo "Downloading from $DOWNLOAD_URL..."
curl -L -o "$TEMP_DIR/$APP_NAME.zip" "$DOWNLOAD_URL"

# Extract
echo "Extracting..."
unzip -q "$TEMP_DIR/$APP_NAME.zip" -d "$TEMP_DIR"

# Find the .app bundle (may be nested in a folder)
APP_PATH=$(find "$TEMP_DIR" -name "*.app" -type d | head -1)
if [ -z "$APP_PATH" ]; then
    echo "Error: Could not find .app bundle in download"
    exit 1
fi

# Remove old version if exists
if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    echo "Removing old version..."
    sudo rm -rf "$INSTALL_DIR/$APP_NAME.app"
fi

# Move to /Applications
echo "Installing to $INSTALL_DIR..."
sudo mv "$APP_PATH" "$INSTALL_DIR/$APP_NAME.app"

# Remove quarantine attribute
echo "Removing quarantine..."
sudo xattr -cr "$INSTALL_DIR/$APP_NAME.app"

echo ""
echo "Installation complete!"
echo ""
echo "IMPORTANT: Grant Accessibility permissions to enable the global hotkey:"
echo "  1. Open System Settings > Privacy & Security > Accessibility"
echo "  2. Add $APP_NAME.app and enable it"
echo ""
echo "To launch: open /Applications/$APP_NAME.app"
