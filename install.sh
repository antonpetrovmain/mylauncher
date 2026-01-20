#!/bin/bash
# MyLauncher Installer
# Downloads and installs MyLauncher, bypassing Gatekeeper
#
# Usage: install.sh [--force|-f]
#   --force, -f  Force reinstall even if same version is installed

set -e

# Parse arguments
FORCE=false
for arg in "$@"; do
    case $arg in
        --force|-f)
            FORCE=true
            ;;
    esac
done

APP_NAME="MyLauncher"
INSTALL_DIR="$HOME/Applications"
REPO="antonpetrovmain/mylauncher"

echo "Installing $APP_NAME..."

# Create ~/Applications if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Get latest release download URL
echo "Finding latest release..."
RELEASE_URL=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep "browser_download_url.*\.zip" | cut -d '"' -f 4)

if [ -z "$RELEASE_URL" ]; then
    echo "Error: Could not find latest release"
    exit 1
fi

# Extract version from filename (e.g., MyLauncher-v0.1.5.zip)
NEW_VERSION=$(echo "$RELEASE_URL" | sed -n 's/.*MyLauncher-v\([0-9.]*\)\.zip/\1/p')

# Check currently installed version
CURRENT_VERSION="not installed"
if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    PLIST="$INSTALL_DIR/$APP_NAME.app/Contents/Info.plist"
    if [ -f "$PLIST" ]; then
        CURRENT_VERSION=$(defaults read "$PLIST" CFBundleShortVersionString 2>/dev/null || echo "unknown")
    fi
fi

echo "Current version: $CURRENT_VERSION"
echo "Installing version: $NEW_VERSION"

# Skip if already up to date (unless --force)
if [ "$CURRENT_VERSION" = "$NEW_VERSION" ] && [ "$FORCE" = false ]; then
    echo "Already up to date! Use --force to reinstall."
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Download latest release
echo "Downloading..."
curl -L -o mylauncher.zip "$RELEASE_URL"

# Extract
echo "Extracting..."
unzip -q mylauncher.zip

# Remove old version if exists
if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    echo "Removing old version..."
    rm -rf "$INSTALL_DIR/$APP_NAME.app"
fi

# Move to Applications
echo "Installing to $INSTALL_DIR..."
mv "$APP_NAME.app" "$INSTALL_DIR/"

# Remove quarantine attribute (bypasses Gatekeeper)
echo "Removing quarantine..."
xattr -cr "$INSTALL_DIR/$APP_NAME.app"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Done! MyLauncher installed to $INSTALL_DIR/$APP_NAME.app"
echo ""
echo "NOTE: You need to grant Accessibility permission:"
echo "  System Settings > Privacy & Security > Accessibility > Add MyLauncher"
echo ""
echo "Run with: open ~/Applications/MyLauncher.app"
