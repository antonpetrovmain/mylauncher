"""Configuration constants for MyLauncher.

Values are loaded from ~/.config/mylauncher/config.toml (created on first run).
"""

from pathlib import Path

from .user_config import get

# History settings (file paths stay in home directory)
COMMAND_HISTORY_FILE = Path.home() / ".mylauncher_history.json"
APP_HISTORY_FILE = Path.home() / ".mylauncher_app_history.json"

# Load from user config with defaults
MAX_COMMAND_HISTORY = get("behavior", "max_command_history", 100)
MAX_APP_HISTORY = get("behavior", "max_app_history", 50)

# Hotkey configuration
HOTKEY_MODIFIERS = get("hotkey", "modifiers", "cmd+ctrl")
HOTKEY_KEY = get("hotkey", "key", "d")

# Execution settings
COMMAND_TIMEOUT_SECONDS = get("behavior", "command_timeout", 10)

# UI dimensions
POPUP_WIDTH = get("popup", "width", 500)
POPUP_HEIGHT = get("popup", "height", 350)
ITEM_ROW_HEIGHT = 20
SEARCH_HEIGHT = 28
MAX_DISPLAY_LEN = 60

# Font settings
FONT_FAMILY = get("popup", "font_family", "Menlo")
FONT_SIZE_INPUT = get("popup", "font_size_input", 14)
FONT_SIZE_TABLE = get("popup", "font_size_table", 12)

# Colors (light mode, dark mode)
COLOR_PALETTE = [
    ("#e8f4f8", "#1a3a4a"),  # blue
    ("#f0e8f8", "#2d1a4a"),  # purple
    ("#e8f8e8", "#1a4a2d"),  # green
    ("#f8f0e8", "#4a3a1a"),  # orange
    ("#f8e8f0", "#4a1a3a"),  # pink
]
SELECTED_BG = ("white", "gray95")
SELECTED_TEXT = ("black", "black")
DEFAULT_TEXT = ("gray10", "gray90")
HOVER_COLOR = ("gray75", "gray25")
