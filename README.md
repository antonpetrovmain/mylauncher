# MyCLI

A macOS menu bar application that provides a command launcher with a global hotkey.

## Features

- **Global Hotkey**: Press `Cmd+Ctrl+D` from anywhere to open the command popup
- **App Suggestions**: Type to filter and quickly launch or focus applications
  - Running apps are shown first and can be focused
  - Installed apps from `/Applications` and `~/Applications` are also suggested
  - Use arrow keys to navigate, Enter to select
- **Shell Commands**: Enter any shell command to execute it
- **Command History**: Recent commands are saved and accessible from the menu bar

## Requirements

- macOS
- Python 3.14+
- Accessibility permissions (System Settings > Privacy & Security > Accessibility)

## Installation

```bash
# Install dependencies
pip install -e .

# Run the application
python -m mycli
# or after install:
mycli
```

## Usage

1. Click the `>_` icon in the menu bar, or press `Cmd+Ctrl+D`
2. Start typing to filter apps, or enter a shell command
3. Use arrow keys to select from suggestions
4. Press Enter to launch/focus the selected app or run the command

## Dependencies

- `rumps`: Menu bar app framework
- `pyobjc-framework-Quartz`: For CGEventTap hotkey capture
- `pyobjc-framework-Cocoa`: For native macOS UI components
- `desktop-notifier`: Cross-platform notifications
