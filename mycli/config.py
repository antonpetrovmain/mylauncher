"""Configuration constants for MyCLI."""

from pathlib import Path

# Hotkey settings
HOTKEY_KEY = "D"
HOTKEY_MODIFIERS = ["Cmd", "Ctrl"]

# History settings
COMMAND_HISTORY_FILE = Path.home() / ".mycli_history.json"
MAX_COMMAND_HISTORY = 100

APP_HISTORY_FILE = Path.home() / ".mycli_app_history.json"
MAX_APP_HISTORY = 50

# Execution settings
COMMAND_TIMEOUT_SECONDS = 10

# UI settings
POPUP_WIDTH = 500
POPUP_HEIGHT = 300
