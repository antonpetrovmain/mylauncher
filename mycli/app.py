"""Main rumps application for MyCLI."""

import signal
import sys

import rumps
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSApp,
    NSApplicationActivateIgnoringOtherApps,
    NSFloatingWindowLevel,
    NSRunningApplication,
    NSTextField,
    NSWorkspace,
)

from mycli.executor import execute_command
from mycli.history import get_recent, save_command
from mycli.hotkey import register_hotkey
from mycli.notifier import notify_failure, notify_success


class MyCLIApp(rumps.App):
    """Menu bar application for MyCLI command launcher."""

    def __init__(self):
        super().__init__(
            name="MyCLI",
            title=">_",
            quit_button=None,
        )
        self._build_menu()
        register_hotkey(self.show_command_popup)

    def _build_menu(self):
        """Build the menu bar menu."""
        self.menu = [
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
                # Truncate long commands for display
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
        # Remove old Recent Commands menu
        if "Recent Commands" in self.menu:
            del self.menu["Recent Commands"]

        # Find the position after "Run Command..." and separator
        # Insert new Recent Commands menu
        new_recent = self._build_recent_menu()

        # Rebuild menu to maintain order
        self.menu.clear()
        self.menu = [
            rumps.MenuItem("Run Command...", callback=self.show_command_popup),
            None,
            new_recent,
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def show_command_popup(self, _=None):
        """Show the command input popup."""
        print(">>> show_command_popup called")
        # Save the previously active application
        previous_app = NSWorkspace.sharedWorkspace().frontmostApplication()

        # Activate the app to bring window to foreground
        NSApp.activateIgnoringOtherApps_(True)
        print(">>> app activated")

        # Create alert with text field
        alert = NSAlert.alloc().init()
        alert.setMessageText_("MyCLI")
        alert.setInformativeText_("Enter command to run:")
        alert.addButtonWithTitle_("Run")
        alert.addButtonWithTitle_("Cancel")

        # Add text input field
        input_field = NSTextField.alloc().initWithFrame_(((0, 0), (400, 24)))
        input_field.setStringValue_("")
        alert.setAccessoryView_(input_field)

        # Make window float on top and focus the input field
        alert.window().setLevel_(NSFloatingWindowLevel)
        alert.window().setInitialFirstResponder_(input_field)
        alert.window().makeKeyAndOrderFront_(None)
        alert.window().makeFirstResponder_(input_field)

        # Show alert
        print(">>> showing alert")
        response = alert.runModal()
        print(f">>> alert response: {response}")

        # Restore focus to the previous application
        if previous_app:
            previous_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

        if response == NSAlertFirstButtonReturn:
            command = input_field.stringValue()
            print(f">>> command entered: '{command}'")
            if command and command.strip():
                self._execute_and_notify(command.strip())

    def _execute_and_notify(self, command: str):
        """Execute a command, save to history, and show notification."""
        print(f">>> executing: {command}")
        result = execute_command(command)
        print(f">>> result: success={result.success}, stdout={result.stdout[:100] if result.stdout else ''}, stderr={result.stderr[:100] if result.stderr else ''}")
        save_command(command)
        self._refresh_recent_menu()

        if result.success:
            output = result.stdout or "(no output)"
            notify_success(command, output)
        else:
            error = result.stderr or f"Exit code: {result.return_code}"
            notify_failure(command, error)


def main():
    """Entry point for MyCLI application."""
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda *args: rumps.quit_application())

    app = MyCLIApp()
    app.run()


if __name__ == "__main__":
    main()
