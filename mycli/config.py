"""Configuration constants for MyCLI."""

from pathlib import Path

# History settings
COMMAND_HISTORY_FILE = Path.home() / ".mycli_history.json"
MAX_COMMAND_HISTORY = 100
APP_HISTORY_FILE = Path.home() / ".mycli_app_history.json"
MAX_APP_HISTORY = 50

# Execution settings
COMMAND_TIMEOUT_SECONDS = 10

# UI dimensions
POPUP_WIDTH = 500
POPUP_HEIGHT = 350
ITEM_ROW_HEIGHT = 20
SEARCH_HEIGHT = 28
MAX_DISPLAY_LEN = 60

# Font settings
FONT_FAMILY = "Menlo"
FONT_SIZE_INPUT = 14
FONT_SIZE_TABLE = 12

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
