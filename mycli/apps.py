"""App discovery and management for MyCLI."""

import json
from pathlib import Path

from AppKit import NSRunningApplication, NSWorkspace

APP_HISTORY_FILE = Path.home() / ".mycli_app_history.json"
MAX_APP_HISTORY = 50


def load_app_history() -> list[str]:
    """Load app history (list of bundle_ids, most recent first)."""
    if not APP_HISTORY_FILE.exists():
        return []
    try:
        with open(APP_HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("apps", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_app_to_history(bundle_id: str) -> None:
    """Record an app as recently used."""
    if not bundle_id:
        return

    apps = load_app_history()

    # Remove if already exists to avoid duplicates
    if bundle_id in apps:
        apps.remove(bundle_id)

    # Add to the beginning (most recent)
    apps.insert(0, bundle_id)

    # Cap at max size
    apps = apps[:MAX_APP_HISTORY]

    try:
        with open(APP_HISTORY_FILE, "w") as f:
            json.dump({"apps": apps}, f, indent=2)
    except IOError:
        pass  # Silently fail if we can't write history


def get_app_recency(bundle_id: str) -> int:
    """Get recency score for an app (lower = more recent, 999 if not in history)."""
    if not bundle_id:
        return 999
    apps = load_app_history()
    try:
        return apps.index(bundle_id)
    except ValueError:
        return 999


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
    Running apps are prioritized and shown first.

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
