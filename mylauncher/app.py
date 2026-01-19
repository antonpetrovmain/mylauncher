"""Main rumps application for MyLauncher."""

from __future__ import annotations

import logging
import multiprocessing
import signal
import subprocess
import sys
import threading
from pathlib import Path

import rumps

from .executor import execute_command
from .history import get_recent, save_command
from .hotkey import register_hotkey
from .notifier import notify_failure, notify_success
from .popup import run_popup

log = logging.getLogger(__name__)

LOG_PATH = Path.home() / "Library/Logs/MyLauncher.log"


def get_app_version() -> str:
    """Get the app version from Info.plist (bundled), package metadata, or __version__."""
    # Try bundled app Info.plist first
    try:
        if getattr(sys, "frozen", False):
            app_path = Path(sys.executable).parent.parent
            plist_path = app_path / "Info.plist"
            if plist_path.exists():
                result = subprocess.run(
                    ["defaults", "read", str(plist_path), "CFBundleShortVersionString"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
    except Exception:
        pass

    # Try importlib.metadata (installed package)
    try:
        from importlib.metadata import version
        return version("mylauncher")
    except Exception:
        pass

    # Fall back to __version__ in package
    try:
        from . import __version__
        return __version__
    except Exception:
        pass

    return "dev"


class MyLauncherApp(rumps.App):
    """Menu bar application for MyLauncher command launcher."""

    def __init__(self):
        super().__init__(
            name="MyLauncher",
            title=">_",
            quit_button=None,
        )
        self._build_menu()
        self._popup_lock = threading.Lock()
        self._popup_process = None
        register_hotkey(self.show_command_popup)

    def _build_menu(self):
        """Build the menu bar menu."""
        version_item = rumps.MenuItem(f"MyLauncher v{get_app_version()}")
        version_item.set_callback(None)  # Disabled
        self.menu = [
            version_item,
            None,  # Separator
            rumps.MenuItem("Run Command...", callback=self.show_command_popup),
            None,  # Separator
            self._build_recent_menu(),
            None,  # Separator
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def _build_recent_menu(self) -> rumps.MenuItem:
        """Build the Recent Commands submenu."""
        recent_menu = rumps.MenuItem("Recent Commands")
        recent_commands = get_recent(10)

        if not recent_commands:
            no_history = rumps.MenuItem("No recent commands")
            no_history.set_callback(None)
            recent_menu.add(no_history)
        else:
            for cmd in recent_commands:
                display_cmd = cmd if len(cmd) <= 40 else cmd[:37] + "..."
                item = rumps.MenuItem(display_cmd, callback=self._make_history_callback(cmd))
                recent_menu.add(item)

        return recent_menu

    def _make_history_callback(self, command: str):
        """Create a callback for a history menu item."""
        def callback(_):
            self._execute_and_notify(command)
        return callback

    def _refresh_recent_menu(self):
        """Refresh the Recent Commands submenu."""
        if "Recent Commands" in self.menu:
            del self.menu["Recent Commands"]

        new_recent = self._build_recent_menu()
        version_item = rumps.MenuItem(f"MyLauncher v{get_app_version()}")
        version_item.set_callback(None)

        self.menu.clear()
        self.menu = [
            version_item,
            None,
            rumps.MenuItem("Run Command...", callback=self.show_command_popup),
            None,
            new_recent,
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def show_command_popup(self, _=None):
        """Show the command input popup."""
        with self._popup_lock:
            if self._popup_process is not None and self._popup_process.is_alive():
                return
            self._popup_process = multiprocessing.Process(target=run_popup)
            self._popup_process.start()

        # Monitor process completion in background thread
        thread = threading.Thread(target=self._wait_for_popup, daemon=True)
        thread.start()

    def _wait_for_popup(self):
        """Wait for popup process to finish."""
        if self._popup_process:
            self._popup_process.join()
            self._refresh_recent_menu()

    def _execute_and_notify(self, command: str):
        """Execute a command, save to history, and show notification."""
        print(f">>> executing: {command}")
        result = execute_command(command)
        print(f">>> result: success={result.success}")
        save_command(command)
        self._refresh_recent_menu()

        if result.success:
            output = result.stdout or "(no output)"
            notify_success(command, output)
        else:
            error = result.stderr or f"Exit code: {result.return_code}"
            notify_failure(command, error)


def main():
    """Entry point for MyLauncher application."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout),
        ],
    )

    version = get_app_version()
    log.info(f"MyLauncher v{version} starting...")

    # Required for PyInstaller multiprocessing support
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

    def signal_handler(*args):
        log.info("Quitting...")
        rumps.quit_application()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = MyLauncherApp()

    timer = rumps.Timer(lambda _: None, 1)
    timer.start()

    app.run()


if __name__ == "__main__":
    main()
