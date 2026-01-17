"""App discovery and management for MyCLI."""

from __future__ import annotations

import json

from AppKit import NSRunningApplication, NSWorkspace
from pathlib import Path

from .config import APP_HISTORY_FILE, MAX_APP_HISTORY


class AppHistory:
    """App usage history storage with persistence."""

    def __init__(self, max_items: int = MAX_APP_HISTORY):
        self._items: list[str] = []
        self._max_items = max_items
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        try:
            if APP_HISTORY_FILE.exists():
                data = json.loads(APP_HISTORY_FILE.read_text())
                self._items = data.get("apps", [])[: self._max_items]
        except Exception:
            self._items = []

    def _save(self) -> None:
        """Save history to disk."""
        try:
            APP_HISTORY_FILE.write_text(
                json.dumps({"apps": self._items}, indent=2)
            )
        except Exception:
            pass

    def add(self, bundle_id: str) -> None:
        """Add an app to history. Moves duplicates to top, trims to max size."""
        if not bundle_id:
            return

        # Remove duplicate if exists
        if bundle_id in self._items:
            self._items.remove(bundle_id)

        # Add to front (newest first)
        self._items.insert(0, bundle_id)

        # Trim to max size
        self._items = self._items[: self._max_items]
        self._save()

    def get_recency(self, bundle_id: str) -> int:
        """Get recency score for an app (lower = more recent, 999 if not in history)."""
        if not bundle_id:
            return 999
        try:
            return self._items.index(bundle_id)
        except ValueError:
            return 999

    def get_all(self) -> list[str]:
        """Get all items in history (newest first)."""
        return self._items.copy()


# Module-level instance for convenience
_app_history = AppHistory()


def load_app_history() -> list[str]:
    """Load app history (list of bundle_ids, most recent first)."""
    return _app_history.get_all()


def save_app_to_history(bundle_id: str) -> None:
    """Record an app as recently used."""
    _app_history.add(bundle_id)


def get_app_recency(bundle_id: str) -> int:
    """Get recency score for an app (lower = more recent, 999 if not in history)."""
    return _app_history.get_recency(bundle_id)


def get_running_apps() -> list[dict]:
    """
    Get currently running apps with their NSRunningApplication objects.

    Returns:
        List of dicts with name, bundle_id, app_obj, and is_running=True
    """
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()

    apps = []
    for app in running_apps:
        # Skip background apps and system processes
        if app.activationPolicy() != 0:  # 0 = NSApplicationActivationPolicyRegular
            continue

        name = app.localizedName()
        if not name:
            continue

        apps.append({
            'name': name,
            'bundle_id': app.bundleIdentifier() or '',
            'app_obj': app,
            'path': None,
            'is_running': True,
        })

    return apps


def get_installed_apps() -> list[dict]:
    """
    Get installed apps from /Applications and ~/Applications.

    Returns:
        List of dicts with name, path, and is_running=False
    """
    apps = []
    seen_names = set()

    # Search both system and user Applications folders
    app_dirs = [
        Path('/Applications'),
        Path.home() / 'Applications',
    ]

    for app_dir in app_dirs:
        if not app_dir.exists():
            continue

        # Find all .app bundles (non-recursive to avoid nested apps)
        for app_path in app_dir.glob('*.app'):
            name = app_path.stem  # Remove .app extension

            # Skip duplicates (prefer first found)
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            apps.append({
                'name': name,
                'bundle_id': None,
                'app_obj': None,
                'path': str(app_path),
                'is_running': False,
            })

    return apps


def get_app_suggestions(filter_text: str = "") -> list[dict]:
    """
    Get combined list of apps: running apps first, then installed.

    Filters by case-insensitive substring match on app name.
    Running apps are prioritized and shown first, sorted by recency.

    Args:
        filter_text: Optional text to filter app names

    Returns:
        List of app dicts, running apps first, then installed
    """
    running = get_running_apps()
    installed = get_installed_apps()

    # Track running app names to avoid duplicates
    running_names = {app['name'].lower() for app in running}

    # Filter installed apps to exclude ones that are running
    installed_filtered = [
        app for app in installed
        if app['name'].lower() not in running_names
    ]

    # Combine: running first, then installed
    all_apps = running + installed_filtered

    # Apply filter if provided
    if filter_text:
        filter_lower = filter_text.lower()
        all_apps = [
            app for app in all_apps
            if filter_lower in app['name'].lower()
        ]

    # Sort: running apps by recency (then alphabetically), other apps alphabetically
    running_apps = sorted(
        [a for a in all_apps if a['is_running']],
        key=lambda x: (get_app_recency(x['bundle_id']), x['name'].lower())
    )
    other_apps = sorted(
        [a for a in all_apps if not a['is_running']],
        key=lambda x: x['name'].lower()
    )

    return running_apps + other_apps


def focus_app(app_obj: NSRunningApplication) -> bool:
    """
    Activate/focus a running app.

    Args:
        app_obj: The NSRunningApplication object

    Returns:
        True if activation succeeded
    """
    return app_obj.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps


def launch_app(app_path: str) -> bool:
    """
    Open/launch an installed app.

    Args:
        app_path: Path to the .app bundle

    Returns:
        True if launch succeeded
    """
    workspace = NSWorkspace.sharedWorkspace()
    return workspace.launchApplication_(app_path)
