"""User configuration file management.

Creates and loads user configuration from ~/.config/mylauncher/config.toml
"""

import logging
import tomllib
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "mylauncher"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = """\
# MyLauncher Configuration
# Edit this file to customize settings. Delete to reset to defaults.

[hotkey]
# Modifiers: cmd, ctrl, alt, shift (separated by +)
modifiers = "cmd+shift"
# Key: letter (a-z) or special key name
# Special keys: tab, space, return, escape, delete, up, down, left, right, f1-f12
key = "tab"

[popup]
width = 500
height = 350
font_family = "Menlo"
font_size_input = 14
font_size_table = 12

[behavior]
command_timeout = 10
max_command_history = 100
max_app_history = 50
"""


def ensure_config_exists() -> None:
    """Create default config file if it doesn't exist."""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(DEFAULT_CONFIG)
        log.info(f"Created default config at {CONFIG_FILE}")


def load_config() -> dict:
    """Load configuration from user config file."""
    ensure_config_exists()
    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        log.warning(f"Failed to load config from {CONFIG_FILE}: {e}")
        return {}


def get(section: str, key: str, default):
    """Get a config value with fallback to default."""
    config = load_config()
    return config.get(section, {}).get(key, default)


def set(section: str, key: str, value) -> bool:
    """Update a config value in the config file.

    Uses line-by-line approach to preserve comments and formatting.
    Returns True if successful.
    """
    ensure_config_exists()
    try:
        content = CONFIG_FILE.read_text()
        lines = content.split('\n')

        # Format the value for TOML
        if isinstance(value, bool):
            toml_value = "true" if value else "false"
        elif isinstance(value, str):
            toml_value = f'"{value}"'
        elif isinstance(value, (int, float)):
            toml_value = str(value)
        else:
            toml_value = f'"{value}"'

        # Find the section and update the key
        in_section = False
        updated = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for section header
            if stripped.startswith('[') and stripped.endswith(']'):
                in_section = stripped == f'[{section}]'
                continue

            # If in the right section, look for the key
            if in_section and (stripped.startswith(f'{key} ') or stripped.startswith(f'{key}=')):
                # Split on = to get key and rest
                if '=' in line:
                    key_part, rest = line.split('=', 1)
                    # Check if there's a comment
                    if '#' in rest:
                        # Preserve the comment
                        value_part, comment = rest.split('#', 1)
                        lines[i] = f'{key_part}= {toml_value}  # {comment.strip()}'
                    else:
                        lines[i] = f'{key_part}= {toml_value}'
                    updated = True
                    break

        if updated:
            CONFIG_FILE.write_text('\n'.join(lines))
            log.info(f"Updated config: [{section}] {key} = {toml_value}")
            return True
        else:
            log.warning(f"Could not find [{section}] {key} in config file")
            return False

    except Exception as e:
        log.error(f"Failed to update config: {e}")
        return False
