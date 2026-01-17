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


def truncate_text(text: str, max_len: int = 60) -> str:
    """Truncate text for display."""
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def run_popup() -> None:
    """Run the popup window."""
    workspace = NSWorkspace.sharedWorkspace()
    previous_app = workspace.frontmostApplication()

    # Set up CustomTkinter (minimal setup for speed)
    ctk.set_appearance_mode("system")

    root = ctk.CTk()
    root.title("MyCLI")

    # Center window on screen
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - POPUP_WIDTH) // 2
    y = (screen_height - POPUP_HEIGHT) // 3
    root.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x}+{y}")
    root.attributes("-topmost", True)

    # Configure grid
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # Fonts
    mono_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TABLE)
    search_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_INPUT)

    # State
    selected_index = [0]
    item_buttons: list[ctk.CTkButton] = []
    current_items: list[dict] = []
    selected_app = [None]
    command_to_run = [None]

    # --- UI Components ---

    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(
        root,
        textvariable=search_var,
        placeholder_text="Search apps or enter command...",
        height=SEARCH_HEIGHT,
        font=search_font,
    )
    search_entry.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
    # Block cursor that doesn't blink
    search_entry._entry.configure(insertwidth=2, insertofftime=0)

    items_frame = ctk.CTkScrollableFrame(root, corner_radius=0)
    items_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
    items_frame.grid_columnconfigure(0, weight=1)

    # Slow down mouse wheel scrolling
    def on_mousewheel(event):
        # Scroll by smaller amount (divide delta by larger number for slower scroll)
        items_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 240)), "units")
        return "break"

    items_frame._parent_canvas.bind("<MouseWheel>", on_mousewheel)
    items_frame.bind("<MouseWheel>", on_mousewheel)

    # --- Item management functions ---

    def scroll_to_selected() -> None:
        """Scroll the items frame to make the selected item visible."""
        if not item_buttons or selected_index[0] >= len(item_buttons):
            return

        button = item_buttons[selected_index[0]]
        # Update to get current geometry
        items_frame.update_idletasks()

        # Get the canvas and its visible region
        canvas = items_frame._parent_canvas
        canvas_height = canvas.winfo_height()

        # Get button position relative to the scrollable frame's interior
        button_y = button.winfo_y()
        button_height = button.winfo_height()

        # Get current scroll position
        scroll_top = canvas.canvasy(0)
        scroll_bottom = scroll_top + canvas_height

        # Check if button is above visible area
        if button_y < scroll_top:
            # Scroll up to show the button
            canvas.yview_moveto(button_y / items_frame._parent_frame.winfo_height())
        # Check if button is below visible area
        elif button_y + button_height > scroll_bottom:
            # Scroll down to show the button
            target = (button_y + button_height - canvas_height) / items_frame._parent_frame.winfo_height()
            canvas.yview_moveto(target)

    def update_selection_highlight() -> None:
        for i, button in enumerate(item_buttons):
            app = current_items[i]
            if i == selected_index[0]:
                color = SELECTED_COLOR
            elif app["is_running"]:
                color = COLOR_RUNNING
            else:
                color = COLOR_INSTALLED
            button.configure(fg_color=color)
        # Scroll to make selected item visible
        scroll_to_selected()

    def select_item(index: int) -> None:
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
        nonlocal current_items
        current_items = items

        for btn in item_buttons:
            btn.destroy()
        item_buttons.clear()

        for i, app in enumerate(items):
            if i == selected_index[0]:
                color = SELECTED_COLOR
            elif app["is_running"]:
                color = COLOR_RUNNING
            else:
                color = COLOR_INSTALLED

            # Display name with running indicator
            display_name = app["name"]
            if app["is_running"]:
                display_name = f"{display_name}  (running)"

            button = ctk.CTkButton(
                items_frame,
                text=truncate_text(display_name),
                anchor="w",
                font=mono_font,
                height=ITEM_ROW_HEIGHT,
                corner_radius=0,
                fg_color=color,
                hover_color=("gray75", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda idx=i: select_item(idx),
            )
            button.grid(row=i, column=0, padx=4, pady=1, sticky="ew")
            item_buttons.append(button)

    # --- Event handlers ---

    def on_search_changed(*args) -> None:
        query = search_var.get()
        items = get_app_suggestions(query)
        selected_index[0] = 0
        update_items_list(items)

    def on_enter(event) -> None:
        if current_items and selected_index[0] < len(current_items):
            select_item(selected_index[0])
        else:
            # No app selected, run as command
            run_as_command()

    def on_escape(event) -> None:
        root.quit()

    def on_arrow_up(event) -> str:
        if selected_index[0] > 0:
            selected_index[0] -= 1
            update_selection_highlight()
        return "break"

    def on_arrow_down(event) -> str:
        if selected_index[0] < len(item_buttons) - 1:
            selected_index[0] += 1
            update_selection_highlight()
        return "break"

    def restore_previous_app() -> None:
        if previous_app:
            time.sleep(0.1)
            previous_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    # Emacs bindings
    def on_clear_all(event) -> str:
        search_var.set("")
        return "break"

    def on_delete_word(event) -> str:
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

    def on_kill_line(event) -> str:
        entry = search_entry._entry
        entry.delete("insert", "end")
        return "break"

    def on_kill_line_backward(event) -> str:
        entry = search_entry._entry
        entry.delete(0, "insert")
        return "break"

    def on_move_beginning(event) -> str:
        search_entry._entry.icursor(0)
        return "break"

    def on_move_end(event) -> str:
        search_entry._entry.icursor("end")
        return "break"

    def on_delete_char(event) -> str:
        search_entry._entry.delete("insert")
        return "break"

    # Bind events
    search_var.trace_add("write", on_search_changed)
    search_entry.bind("<Return>", on_enter)
    search_entry.bind("<Escape>", on_escape)
    search_entry.bind("<Up>", on_arrow_up)
    search_entry.bind("<Down>", on_arrow_down)
    # macOS shortcuts
    search_entry.bind("<Command-BackSpace>", on_clear_all)
    search_entry.bind("<Option-BackSpace>", on_delete_word)
    # Emacs bindings
    search_entry.bind("<Control-w>", on_delete_word)
    search_entry.bind("<Control-u>", on_kill_line_backward)
    search_entry.bind("<Control-k>", on_kill_line)
    search_entry.bind("<Control-a>", on_move_beginning)
    search_entry.bind("<Control-e>", on_move_end)
    search_entry.bind("<Control-d>", on_delete_char)
    search_entry.bind("<Control-p>", on_arrow_up)
    search_entry.bind("<Control-n>", on_arrow_down)
    root.bind("<Escape>", on_escape)
    root.protocol("WM_DELETE_WINDOW", root.quit)

    # Show window immediately (before loading apps for faster perceived startup)
    root.deiconify()
    root.lift()
    root.focus_force()
    search_entry.focus_set()

    # Load apps after window is visible (deferred for speed)
    def load_initial_items():
        initial_items = get_app_suggestions("")
        update_items_list(initial_items)

    root.after(1, load_initial_items)

    # Run event loop
    root.mainloop()
    root.destroy()

    # Handle the result
    app = selected_app[0]
    cmd = command_to_run[0]

    if app:
        # An app was selected
        if app["is_running"]:
            save_app_to_history(app["bundle_id"])
            focus_app(app["app_obj"])
        else:
            save_app_to_history(app.get("bundle_id") or app["name"])
            launch_app(app["path"])
    elif cmd:
        # Run as shell command
        launch_command(cmd)
        save_command(cmd)
        restore_previous_app()
    else:
        # Nothing selected, restore previous app
        restore_previous_app()


if __name__ == "__main__":
    run_popup()
