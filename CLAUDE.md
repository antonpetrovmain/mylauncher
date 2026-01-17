# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyCLI is a macOS menu bar application that provides a command launcher with a global hotkey. It runs shell commands from a popup window, displays results, and shows macOS notifications for success/failure.

## Development Commands

```bash
# Install dependencies (requires Python 3.14+)
pip install -e .

# Run the application
python -m mycli
# or after install:
mycli
```

## Architecture

The application uses `rumps` for the menu bar interface combined with PyObjC for native macOS UI components.

### Module Responsibilities

- **app.py**: Main `rumps.App` subclass (`MyCLIApp`). Creates the menu bar icon, builds menus, and handles the command input popup using native `NSPanel`/`NSTextField`. Runs a modal dialog for command input.
- **executor.py**: Runs shell commands via subprocess in a new session group. Sources `~/.zshrc` for PATH, has 10-second timeout, and kills process groups on timeout.
- **hotkey.py**: Global hotkey (Cmd+Ctrl+D) using `CGEventTap`. Runs in a background thread and calls back to the main thread via `AppHelper.callAfter`.
- **history.py**: JSON-based command history stored at `~/.mycli_history.json`. Maintains up to 100 commands, deduplicates entries.
- **notifier.py**: Async wrapper around `desktop-notifier` for success/failure notifications.

### Key Implementation Details

- The popup uses `NSApp.runModalForWindow_()` which blocks until Enter is pressed or window closes
- Commands execute in user's home directory with their shell environment
- Signal handlers (SIGINT/SIGTERM) enable graceful Ctrl+C shutdown
- A 1-second timer keeps the run loop responsive to signals

## Dependencies

- `rumps`: Menu bar app framework
- `pyobjc-framework-Quartz`: For CGEventTap hotkey capture
- `desktop-notifier`: Cross-platform notifications

## Requirements

Accessibility permissions required for global hotkey: System Settings > Privacy & Security > Accessibility
