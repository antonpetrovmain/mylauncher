"""Command history management for MyCLI."""

from __future__ import annotations

import json

from .config import COMMAND_HISTORY_FILE, MAX_COMMAND_HISTORY


class CommandHistory:
    """Command history storage with persistence."""

    def __init__(self, max_items: int = MAX_COMMAND_HISTORY):
        self._items: list[str] = []
        self._max_items = max_items
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        try:
            if COMMAND_HISTORY_FILE.exists():
                data = json.loads(COMMAND_HISTORY_FILE.read_text())
                self._items = data.get("commands", [])[: self._max_items]
        except Exception:
            self._items = []

    def _save(self) -> None:
        """Save history to disk."""
        try:
            COMMAND_HISTORY_FILE.write_text(
                json.dumps({"commands": self._items}, indent=2)
            )
        except Exception:
            pass

    def add(self, command: str) -> None:
        """Add a command to history. Moves duplicates to top, trims to max size."""
        if not command or not command.strip():
            return

        # Remove duplicate if exists
        if command in self._items:
            self._items.remove(command)

        # Add to front (newest first)
        self._items.insert(0, command)

        # Trim to max size
        self._items = self._items[: self._max_items]
        self._save()

    def get_recent(self, limit: int = 10) -> list[str]:
        """Get the most recent commands."""
        return self._items[:limit]

    def get_all(self) -> list[str]:
        """Get all items in history (newest first)."""
        return self._items.copy()


# Module-level instance for convenience
_history = CommandHistory()


def load_history() -> list[str]:
    """Load command history from file."""
    return _history.get_all()


def save_command(command: str) -> None:
    """Save a command to history, avoiding duplicates at the top."""
    _history.add(command)


def get_recent(limit: int = 10) -> list[str]:
    """Get the most recent commands."""
    return _history.get_recent(limit)
