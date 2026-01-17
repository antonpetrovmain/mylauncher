"""Command history management for MyCLI."""

import json
from pathlib import Path
from typing import List

HISTORY_FILE = Path.home() / ".mycli_history.json"
MAX_HISTORY_SIZE = 100


def load_history() -> List[str]:
    """Load command history from file."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("commands", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_command(command: str) -> None:
    """Save a command to history, avoiding duplicates at the top."""
    commands = load_history()

    # Remove command if it already exists to avoid duplicates
    if command in commands:
        commands.remove(command)

    # Add to the beginning
    commands.insert(0, command)

    # Cap at max size
    commands = commands[:MAX_HISTORY_SIZE]

    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({"commands": commands}, f, indent=2)
    except IOError:
        pass  # Silently fail if we can't write history


def get_recent(limit: int = 10) -> List[str]:
    """Get the most recent commands."""
    commands = load_history()
    return commands[:limit]
