# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyLauncher is a macOS menu bar application that provides an app launcher and command runner with a global hotkey (Cmd+Ctrl+D). It shows running apps first (sorted by recent usage), supports app search, and can execute shell commands.

## Development Commands

```bash
# Install dependencies (requires Python 3.14+)
pip install -e .

# Run the application
python -m mylauncher
# or after install:
mylauncher

# Build macOS .app bundle (requires pyinstaller, pillow)
pip install pyinstaller pillow
./scripts/build_app.sh
# Output: dist/MyLauncher.app

# Debug hotkey detection
python test_hotkey.py
```

## Architecture

The application uses `rumps` for the menu bar interface combined with PyObjC for native macOS UI components. The popup runs in a separate process via `multiprocessing` to avoid Tkinter/PyObjC threading conflicts.

### Module Responsibilities

- **app.py**: Main `rumps.App` subclass (`MyLauncherApp`). Creates the menu bar icon, builds menus, spawns popup process, and handles command execution with notifications.
- **popup.py**: CustomTkinter-based popup window with app list and search. Runs in a separate process; communicates result back via `multiprocessing.Queue`.
- **apps.py**: App discovery using `NSWorkspace`. `AppHistory` tracks usage for sorting (stored at `~/.mylauncher_app_history.json`). Returns running apps first (sorted by recency), then installed apps from /System/Applications, /Applications, and ~/Applications.
- **executor.py**: Runs shell commands via subprocess in a new session group. Sources `~/.zshrc` for PATH, has 10-second timeout, and kills process groups on timeout.
- **hotkey.py**: Global hotkey (Cmd+Ctrl+D) using `CGEventTap`. Runs in a background thread and calls back to the main thread via `AppHelper.callAfter`.
- **history.py**: JSON-based command history stored at `~/.mylauncher_history.json`. Maintains up to 100 commands, deduplicates entries.
- **notifier.py**: Async wrapper around `desktop-notifier` for success/failure notifications.
- **config.py**: All constants (dimensions, timeouts, colors, file paths).

### Key Implementation Details

- The popup uses `multiprocessing.Process` because Tkinter must run on the main thread but rumps also needs the main thread
- Commands execute in user's home directory with their shell environment
- Signal handlers (SIGINT/SIGTERM) enable graceful Ctrl+C shutdown
- A 1-second timer keeps the run loop responsive to signals

## Dependencies

- `rumps`: Menu bar app framework
- `pyobjc-framework-Quartz`: For CGEventTap hotkey capture
- `pyobjc-framework-Cocoa`: For NSWorkspace app discovery
- `customtkinter`: Popup window UI
- `desktop-notifier`: Cross-platform notifications

## Requirements

Accessibility permissions required for global hotkey: System Settings > Privacy & Security > Accessibility
