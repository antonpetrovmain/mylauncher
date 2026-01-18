"""App discovery and management for MyLauncher."""

from __future__ import annotations

import json
from pathlib import Path

from AppKit import NSRunningApplication, NSWorkspace

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


_installed_apps_cache: list[dict] | None = None


def get_installed_apps(use_cache: bool = True) -> list[dict]:
    """
    Get installed apps from /Applications and ~/Applications.

    Args:
        use_cache: If True, return cached results if available (faster)

    Returns:
        List of dicts with name, path, is_running=False, name_lower (pre-sorted alphabetically)
    """
    global _installed_apps_cache

    if use_cache and _installed_apps_cache is not None:
        return _installed_apps_cache

    apps = []
    seen_names = set()

    # Search system and user Applications folders
    app_dirs = [
        Path('/System/Applications'),
        Path('/Applications'),
        Path.home() / 'Applications',
    ]

    for app_dir in app_dirs:
        if not app_dir.exists():
            continue

        # Find all .app bundles (non-recursive to avoid nested apps)
        for app_path in app_dir.glob('*.app'):
            name = app_path.stem  # Remove .app extension
            name_lower = name.lower()

            # Skip duplicates (prefer first found)
            if name_lower in seen_names:
                continue
            seen_names.add(name_lower)

            apps.append({
                'name': name,
                'name_lower': name_lower,  # Cache lowercase for faster filtering
                'bundle_id': None,
                'app_obj': None,
                'path': str(app_path),
                'is_running': False,
            })

    # Pre-sort alphabetically so we don't need to sort each time
    apps.sort(key=lambda x: x['name_lower'])
    _installed_apps_cache = apps
    return apps


def get_running_app_suggestions(filter_text: str = "") -> list[dict]:
    """
    Get running apps only, sorted by recency.

    Args:
        filter_text: Optional text to filter app names

    Returns:
        List of running app dicts sorted by recency
    """
    running = get_running_apps()
    filter_lower = filter_text.lower() if filter_text else ""

    if filter_lower:
        running = [app for app in running if filter_lower in app['name'].lower()]

    # Use dict for O(1) recency lookup instead of O(n) list.index()
    recency_map = {bid: i for i, bid in enumerate(_app_history._items)}

    return sorted(
        running,
        key=lambda x: (recency_map.get(x['bundle_id'], 999), x['name'].lower())
    )


def get_all_app_suggestions(filter_text: str = "") -> list[dict]:
    """
    Get all apps: running first, then installed.

    Args:
        filter_text: Optional text to filter app names

    Returns:
        List of app dicts, running apps first, then installed
    """
    running = get_running_apps()
    installed = get_installed_apps()

    running_names = {app['name'].lower() for app in running}
    filter_lower = filter_text.lower() if filter_text else ""

    if filter_lower:
        installed_filtered = [
            app for app in installed
            if app['name_lower'] not in running_names and filter_lower in app['name_lower']
        ]
        running_filtered = [
            app for app in running
            if filter_lower in app['name'].lower()
        ]
    else:
        installed_filtered = [
            app for app in installed
            if app['name_lower'] not in running_names
        ]
        running_filtered = running

    running_sorted = sorted(
        running_filtered,
        key=lambda x: (get_app_recency(x['bundle_id']), x['name'].lower())
    )

    return running_sorted + installed_filtered


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
