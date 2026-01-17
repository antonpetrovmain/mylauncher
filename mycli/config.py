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
POPUP_HEIGHT = 350
ITEM_ROW_HEIGHT = 22
SEARCH_HEIGHT = 28

# Font settings
FONT_FAMILY = "Menlo"
FONT_SIZE_INPUT = 14
FONT_SIZE_TABLE = 12
FONT_SIZE_LABEL = 12

# Colors for app list (light mode, dark mode)
COLOR_RUNNING = ("#e8f4e8", "#1a4a2d")  # soft green for running apps
COLOR_INSTALLED = ("#f0f0f0", "#2a2a2a")  # gray for installed apps
SELECTED_COLOR = ("gray70", "gray30")
