"""Main rumps application for MyCLI."""

from __future__ import annotations

import signal

import rumps
from AppKit import (
    NSApp,
    NSApplicationActivateIgnoringOtherApps,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSBezierPath,
    NSColor,
    NSFloatingWindowLevel,
    NSFont,
    NSMakeRect,
    NSPanel,
    NSRectFill,
    NSScreen,
    NSScrollView,
    NSTableColumn,
    NSTableView,
    NSTextField,
    NSTextView,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
    NSWorkspace,
)

import objc
from Foundation import NSIndexSet, NSObject, NSRange

from .apps import focus_app, get_app_suggestions, launch_app, save_app_to_history
from .config import (
    FONT_FAMILY,
    FONT_SIZE_INPUT,
    FONT_SIZE_LABEL,
    FONT_SIZE_TABLE,
    POPUP_HEIGHT,
    POPUP_WIDTH,
)
from .executor import execute_command, launch_command
from .history import get_recent, save_command
from .hotkey import register_hotkey
from .notifier import notify_failure, notify_success


class BlockCursorFieldEditor(NSTextView):
    """Custom field editor that draws a non-blinking block cursor."""

    def updateInsertionPointStateAndRestartTimer_(self, restart):
        """Override to prevent cursor blinking by never restarting the blink timer."""
        # Call super but always with restart=False to stop blinking
        objc.super(BlockCursorFieldEditor, self).updateInsertionPointStateAndRestartTimer_(False)

    def setInsertionPointColor_(self, color):
        """Set cursor color and ensure it's visible."""
        objc.super(BlockCursorFieldEditor, self).setInsertionPointColor_(color)

    def drawInsertionPointInRect_color_turnedOn_(self, rect, color, flag):
        """Override to always draw the cursor (ignore turnedOn flag)."""
        # Always draw as if turned on
        objc.super(BlockCursorFieldEditor, self).drawInsertionPointInRect_color_turnedOn_(
            rect, color, True
        )


class WindowDelegate(NSObject):
    """Delegate to handle window close and provide custom field editor."""

    _fieldEditor = objc.ivar()

    def init(self):
        self = objc.super(WindowDelegate, self).init()
        if self is None:
            return None
        # Create the custom field editor
        self._fieldEditor = BlockCursorFieldEditor.alloc().initWithFrame_(
            NSMakeRect(0, 0, 100, 20)
        )
        self._fieldEditor.setFieldEditor_(True)
        return self

    def windowWillClose_(self, notification):
        """Called when window is closing."""
        NSApp.stopModal()

    def windowWillReturnFieldEditor_toObject_(self, sender, client):
        """Return our custom block cursor field editor."""
        print(f">>> windowWillReturnFieldEditor called for {client}")
        return self._fieldEditor


class SuggestionDelegate(NSObject):
    """Delegate for text field and suggestion table."""

    @objc.python_method
    def _setup(self, table_view, input_field):
        """Set up with references to table and input field (Python-only method)."""
        self.table_view = table_view
        self.input_field = input_field
        self.suggestions = []
        self.selected_app = None
        self._update_suggestions("")

    @objc.python_method
    def _update_suggestions(self, filter_text):
        """Update the suggestions list based on filter text."""
        self.suggestions = get_app_suggestions(filter_text)
        self.table_view.reloadData()
        # Select first row if there are suggestions
        if self.suggestions:
            self.table_view.selectRowIndexes_byExtendingSelection_(
                NSIndexSet.indexSetWithIndex_(0), False
            )

    def controlTextDidChange_(self, notification):
        """Called when text changes in the input field."""
        text = self.input_field.stringValue()
        self._update_suggestions(text)

    def controlTextDidEndEditing_(self, notification):
        """Called when editing ends (Enter pressed)."""
        # Check if an app is selected in the table
        selected_row = self.table_view.selectedRow()
        if selected_row >= 0 and selected_row < len(self.suggestions):
            self.selected_app = self.suggestions[selected_row]
        else:
            self.selected_app = None
        NSApp.stopModal()

    def control_textView_doCommandBySelector_(self, control, text_view, selector):
        """Handle special key commands like arrow keys and Emacs bindings."""
        selector_name = str(selector)

        # Arrow down / Ctrl+N - move selection down
        if selector_name == 'moveDown:':
            current = self.table_view.selectedRow()
            if current < len(self.suggestions) - 1:
                self.table_view.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(current + 1), False
                )
                self.table_view.scrollRowToVisible_(current + 1)
            return True

        # Arrow up / Ctrl+P - move selection up
        if selector_name == 'moveUp:':
            current = self.table_view.selectedRow()
            if current > 0:
                self.table_view.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(current - 1), False
                )
                self.table_view.scrollRowToVisible_(current - 1)
            return True

        # Ctrl+A - move to beginning of line
        if selector_name == 'moveToBeginningOfLine:':
            text_view.setSelectedRange_((0, 0))
            return True

        # Ctrl+E - move to end of line
        if selector_name == 'moveToEndOfLine:':
            length = len(text_view.string())
            text_view.setSelectedRange_((length, 0))
            return True

        # Ctrl+K - delete to end of line
        if selector_name in ('deleteToEndOfLine:', 'deleteToEndOfParagraph:'):
            text = text_view.string()
            selection = text_view.selectedRange()
            cursor = selection.location
            text_view.setString_(text[:cursor])
            return True

        # Ctrl+U - delete to beginning of line
        if selector_name == 'deleteToBeginningOfLine:':
            text = text_view.string()
            selection = text_view.selectedRange()
            cursor = selection.location
            text_view.setString_(text[cursor:])
            text_view.setSelectedRange_((0, 0))
            return True

        # Ctrl+W / Option+Backspace - delete word backward
        if selector_name == 'deleteWordBackward:':
            text = text_view.string()
            selection = text_view.selectedRange()
            cursor = selection.location
            # Skip trailing spaces
            pos = cursor
            while pos > 0 and text[pos - 1] == ' ':
                pos -= 1
            # Delete word
            while pos > 0 and text[pos - 1] != ' ':
                pos -= 1
            text_view.setString_(text[:pos] + text[cursor:])
            text_view.setSelectedRange_((pos, 0))
            return True

        # Ctrl+D - delete character forward
        if selector_name == 'deleteForward:':
            text = text_view.string()
            selection = text_view.selectedRange()
            cursor = selection.location
            if cursor < len(text):
                text_view.setString_(text[:cursor] + text[cursor + 1:])
                text_view.setSelectedRange_((cursor, 0))
            return True

        # Escape - cancel
        if selector_name == 'cancelOperation:':
            NSApp.stopModal()
            return True

        return False

    # NSTableViewDataSource methods
    def numberOfRowsInTableView_(self, table_view):
        """Return number of rows in table."""
        return len(self.suggestions)

    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        """Return value for a cell."""
        if row >= len(self.suggestions):
            return ""
        app = self.suggestions[row]
        name = app['name']
        if app['is_running']:
            return f"{name}  (running)"
        return name

    # NSTableViewDelegate method for double-click/selection
    def tableViewSelectionDidChange_(self, notification):
        """Called when table selection changes."""
        pass  # Selection is handled on Enter key


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
        """Show the command input popup with app suggestions."""
        print(">>> show_command_popup called")
        # Save the previously active application
        previous_app = NSWorkspace.sharedWorkspace().frontmostApplication()

        # Activate the app to bring window to foreground
        NSApp.activateIgnoringOtherApps_(True)

        # Create panel window (taller to fit suggestions)
        screen = NSScreen.mainScreen()
        screen_rect = screen.frame()
        x = screen_rect.origin.x + (screen_rect.size.width - POPUP_WIDTH) / 2
        y = screen_rect.origin.y + (screen_rect.size.height - POPUP_HEIGHT) / 2

        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, POPUP_WIDTH, POPUP_HEIGHT),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        panel.setTitle_("MyCLI")
        panel.setLevel_(NSFloatingWindowLevel)

        # Set window delegate to handle close button
        window_delegate = WindowDelegate.alloc().init()
        panel.setDelegate_(window_delegate)

        content_view = panel.contentView()

        # Create fonts
        label_font = NSFont.fontWithName_size_(FONT_FAMILY, FONT_SIZE_LABEL)
        input_font = NSFont.fontWithName_size_(FONT_FAMILY, FONT_SIZE_INPUT)

        # Create input label
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, POPUP_HEIGHT - 35, 460, 20))
        label.setStringValue_("Enter command:")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setFont_(label_font)
        content_view.addSubview_(label)

        # Create input field with monospace font
        input_field = NSTextField.alloc().initWithFrame_(NSMakeRect(20, POPUP_HEIGHT - 60, 460, 24))
        input_field.setStringValue_("")
        input_field.setFont_(input_font)
        content_view.addSubview_(input_field)

        # Create suggestion table
        table_height = 200
        scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(20, 20, 460, table_height)
        )
        scroll_view.setBorderType_(NSBezelBorder)
        scroll_view.setHasVerticalScroller_(True)

        table_view = NSTableView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 460, table_height)
        )

        # Add column for app names with monospace font
        table_font = NSFont.fontWithName_size_(FONT_FAMILY, FONT_SIZE_TABLE)
        column = NSTableColumn.alloc().initWithIdentifier_("app")
        column.setWidth_(440)
        column.headerCell().setStringValue_("Suggestions")
        column.dataCell().setFont_(table_font)
        table_view.addTableColumn_(column)
        table_view.setHeaderView_(None)  # Hide header
        table_view.setRowHeight_(18.0)  # Slightly taller rows for readability

        scroll_view.setDocumentView_(table_view)
        content_view.addSubview_(scroll_view)

        # Create and set delegate (handles both text field and table)
        suggestion_delegate = SuggestionDelegate.alloc().init()
        suggestion_delegate._setup(table_view, input_field)
        input_field.setDelegate_(suggestion_delegate)
        table_view.setDataSource_(suggestion_delegate)
        table_view.setDelegate_(suggestion_delegate)

        # Focus input field
        panel.makeKeyAndOrderFront_(None)
        panel.makeFirstResponder_(input_field)

        # Run modal (will stop when Enter is pressed or window closes)
        NSApp.runModalForWindow_(panel)

        # Get command after modal ends
        command = input_field.stringValue().strip()
        selected_app = suggestion_delegate.selected_app
        print(f">>> command entered: '{command}', selected_app: {selected_app}")

        # Handle the action
        if selected_app:
            # An app was selected from suggestions
            if selected_app['is_running']:
                print(f">>> focusing app: {selected_app['name']}")
                save_app_to_history(selected_app['bundle_id'])
                focus_app(selected_app['app_obj'])
            else:
                print(f">>> launching app: {selected_app['path']}")
                # For installed apps, use bundle_id if available, otherwise app name
                save_app_to_history(selected_app.get('bundle_id') or selected_app['name'])
                launch_app(selected_app['path'])
        elif command:
            # No app selected, treat as shell command
            print(f">>> launching command: {command}")
            launch_command(command)
            save_command(command)
            self._refresh_recent_menu()

        # Close panel
        panel.close()

        # Restore focus to the previous application (only if no app action taken)
        if previous_app and not selected_app:
            previous_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

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
    def signal_handler(*args):
        print("\nQuitting...")
        rumps.quit_application()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = MyCLIApp()

    # Timer to allow Python to process signals
    timer = rumps.Timer(lambda _: None, 1)
    timer.start()

    app.run()


if __name__ == "__main__":
    main()
