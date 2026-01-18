"""Standalone popup runner using customtkinter."""

from __future__ import annotations

import time

import customtkinter as ctk
from AppKit import NSApplicationActivateIgnoringOtherApps, NSWorkspace

from .apps import focus_app, get_app_suggestions, launch_app, save_app_to_history
from .config import (
    COLOR_INSTALLED,
    COLOR_RUNNING,
    FONT_FAMILY,
    FONT_SIZE_INPUT,
    FONT_SIZE_TABLE,
    ITEM_ROW_HEIGHT,
    POPUP_HEIGHT,
    POPUP_WIDTH,
    SEARCH_HEIGHT,
    SELECTED_COLOR,
)
from .executor import launch_command
from .history import save_command

MAX_DISPLAY_LEN = 60


def get_item_color(app: dict, is_selected: bool) -> tuple[str, str]:
    """Get the background color for an item based on its state."""
    if is_selected:
        return SELECTED_COLOR
    if app["is_running"]:
        return COLOR_RUNNING
    return COLOR_INSTALLED


def run_popup() -> None:
    """Run the popup window."""
    workspace = NSWorkspace.sharedWorkspace()
    previous_app = workspace.frontmostApplication()

    ctk.set_appearance_mode("system")

    root = ctk.CTk()
    root.withdraw()
    root.title("")

    # Center window on screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - POPUP_WIDTH) // 2
    y = (screen_height - POPUP_HEIGHT) // 3
    root.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x}+{y}")
    root.attributes("-topmost", True)

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    mono_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TABLE)
    search_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_INPUT)

    # Mutable state (start at index 1 for quick switching to previous app)
    selected_index = [1]
    item_buttons: list[ctk.CTkButton] = []
    current_items: list[dict] = []
    selected_app = [None]
    command_to_run = [None]

    # Search entry
    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(
        root,
        textvariable=search_var,
        placeholder_text="Search apps or enter command...",
        height=SEARCH_HEIGHT,
        font=search_font,
    )
    search_entry.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
    search_entry._entry.configure(insertwidth=2, insertofftime=0)

    # Scrollable items list
    items_frame = ctk.CTkScrollableFrame(root, corner_radius=0)
    items_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
    items_frame.grid_columnconfigure(0, weight=1)

    def on_mousewheel(event):
        items_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 240)), "units")
        return "break"

    items_frame._parent_canvas.bind("<MouseWheel>", on_mousewheel)
    items_frame.bind("<MouseWheel>", on_mousewheel)

    def scroll_to_selected() -> None:
        """Ensure the selected item is visible in the scroll area."""
        if not item_buttons or selected_index[0] >= len(item_buttons):
            return

        button = item_buttons[selected_index[0]]
        items_frame.update_idletasks()

        # Get the inner frame that contains all buttons
        inner_frame = items_frame._parent_frame
        canvas = items_frame._parent_canvas

        # Get actual positions
        button_top = button.winfo_y()
        button_bottom = button_top + button.winfo_height()

        # Get visible region in canvas coordinates
        visible_top = int(canvas.canvasy(0))
        visible_bottom = visible_top + canvas.winfo_height()

        # Get total scrollable height
        total_height = inner_frame.winfo_reqheight()
        if total_height <= 0:
            return

        # Scroll if button is outside visible area
        if button_top < visible_top:
            fraction = max(0.0, button_top / total_height)
            canvas.yview_moveto(fraction)
        elif button_bottom > visible_bottom:
            fraction = max(0.0, (button_bottom - canvas.winfo_height()) / total_height)
            canvas.yview_moveto(fraction)

    def update_selection_highlight() -> None:
        """Update button colors to reflect current selection."""
        for i, button in enumerate(item_buttons):
            button.configure(fg_color=get_item_color(current_items[i], i == selected_index[0]))
        scroll_to_selected()

    def select_item(index: int) -> None:
        """Select an item and close the popup."""
        if 0 <= index < len(current_items):
            selected_app[0] = current_items[index]
            root.quit()

    def run_as_command() -> None:
        """Run the search text as a shell command."""
        cmd = search_var.get().strip()
        if cmd:
            command_to_run[0] = cmd
            root.quit()

    def update_items_list(items: list[dict]) -> None:
        """Rebuild the items list with new data."""
        nonlocal current_items
        current_items = items

        # Clamp selected index to valid range
        if selected_index[0] >= len(items):
            selected_index[0] = max(0, len(items) - 1)

        for btn in item_buttons:
            btn.destroy()
        item_buttons.clear()

        for i, app in enumerate(items):
            display_name = app["name"]
            if app["is_running"]:
                display_name = f"{display_name}  (running)"
            if len(display_name) > MAX_DISPLAY_LEN:
                display_name = display_name[: MAX_DISPLAY_LEN - 3] + "..."

            button = ctk.CTkButton(
                items_frame,
                text=display_name,
                anchor="w",
                font=mono_font,
                height=ITEM_ROW_HEIGHT,
                corner_radius=0,
                fg_color=get_item_color(app, i == selected_index[0]),
                hover_color=("gray75", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda idx=i: select_item(idx),
            )
            button.grid(row=i, column=0, padx=4, pady=1, sticky="ew")
            item_buttons.append(button)

    def restore_previous_app() -> None:
        """Restore focus to the previously active app."""
        if previous_app:
            time.sleep(0.1)
            previous_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    # Event handlers
    def on_search_changed(*_) -> None:
        selected_index[0] = 0
        update_items_list(get_app_suggestions(search_var.get()))

    def on_enter(_) -> None:
        if current_items and selected_index[0] < len(current_items):
            select_item(selected_index[0])
        else:
            run_as_command()

    def on_escape(_) -> None:
        root.quit()

    def on_arrow_up(_) -> str:
        if selected_index[0] > 0:
            selected_index[0] -= 1
            update_selection_highlight()
        return "break"

    def on_arrow_down(_) -> str:
        if selected_index[0] < len(item_buttons) - 1:
            selected_index[0] += 1
            update_selection_highlight()
        return "break"

    def on_clear_all(_) -> str:
        search_var.set("")
        return "break"

    def on_delete_word(_) -> str:
        entry = search_entry._entry
        cursor = entry.index("insert")
        text = search_var.get()
        pos = cursor
        while pos > 0 and text[pos - 1] == " ":
            pos -= 1
        while pos > 0 and text[pos - 1] != " ":
            pos -= 1
        entry.delete(pos, cursor)
        return "break"

    def on_kill_line(_) -> str:
        search_entry._entry.delete("insert", "end")
        return "break"

    def on_kill_line_backward(_) -> str:
        search_entry._entry.delete(0, "insert")
        return "break"

    def on_move_beginning(_) -> str:
        search_entry._entry.icursor(0)
        return "break"

    def on_move_end(_) -> str:
        search_entry._entry.icursor("end")
        return "break"

    def on_delete_char(_) -> str:
        search_entry._entry.delete("insert")
        return "break"

    # Keybindings
    search_var.trace_add("write", on_search_changed)
    search_entry.bind("<Return>", on_enter)
    search_entry.bind("<Escape>", on_escape)
    search_entry.bind("<Up>", on_arrow_up)
    search_entry.bind("<Down>", on_arrow_down)
    search_entry.bind("<Command-BackSpace>", on_clear_all)
    search_entry.bind("<Option-BackSpace>", on_delete_word)
    search_entry.bind("<Control-w>", on_delete_word)
    search_entry.bind("<Control-u>", on_kill_line_backward)
    search_entry.bind("<Control-k>", on_kill_line)
    search_entry.bind("<Control-a>", on_move_beginning)
    search_entry.bind("<Control-e>", on_move_end)
    search_entry.bind("<Control-d>", on_delete_char)
    search_entry.bind("<Control-p>", on_arrow_up)
    search_entry.bind("<Control-n>", on_arrow_down)
    root.bind("<Escape>", on_escape)

    # Show window and focus
    root.deiconify()
    root.lift()
    root.focus_force()
    search_entry.focus_set()

    # Defer loading items for faster perceived startup
    root.after(1, lambda: update_items_list(get_app_suggestions("")))

    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass

    # Handle result
    app = selected_app[0]
    cmd = command_to_run[0]

    if app:
        save_app_to_history(app.get("bundle_id") or app["name"])
        if app["is_running"]:
            focus_app(app["app_obj"])
        else:
            launch_app(app["path"])
    elif cmd:
        launch_command(cmd)
        save_command(cmd)
        restore_previous_app()
    else:
        restore_previous_app()


if __name__ == "__main__":
    run_popup()
