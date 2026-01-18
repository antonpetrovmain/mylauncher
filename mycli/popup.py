"""Standalone popup runner using customtkinter."""

from __future__ import annotations

import time

import customtkinter as ctk
from AppKit import NSApplicationActivateIgnoringOtherApps, NSWorkspace

from .apps import focus_app, get_app_suggestions, launch_app, save_app_to_history
from .config import (
    COLOR_PALETTE,
    DEFAULT_TEXT,
    FONT_FAMILY,
    FONT_SIZE_INPUT,
    FONT_SIZE_TABLE,
    HOVER_COLOR,
    ITEM_ROW_HEIGHT,
    MAX_DISPLAY_LEN,
    POPUP_HEIGHT,
    POPUP_WIDTH,
    SEARCH_HEIGHT,
    SELECTED_BG,
    SELECTED_TEXT,
)
from .executor import launch_command
from .history import save_command


def run_popup() -> None:
    """Run the popup window."""
    workspace = NSWorkspace.sharedWorkspace()
    previous_app = workspace.frontmostApplication()

    ctk.set_appearance_mode("system")

    root = ctk.CTk()
    root.withdraw()
    root.title("")

    # Center window on screen
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (screen_w - POPUP_WIDTH) // 2, (screen_h - POPUP_HEIGHT) // 3
    root.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x}+{y}")
    root.attributes("-topmost", True)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    mono_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TABLE)
    search_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_INPUT)

    # State
    selected_idx = [1]  # Start at 1 for quick app switching
    buttons: list[ctk.CTkButton] = []
    items: list[dict] = []
    result_app = [None]
    result_cmd = [None]

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

    # Items list
    items_frame = ctk.CTkScrollableFrame(root, corner_radius=0)
    items_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
    items_frame.grid_columnconfigure(0, weight=1)

    def on_mousewheel(event):
        items_frame._parent_canvas.yview_scroll(int(-event.delta / 240), "units")
        return "break"

    items_frame._parent_canvas.bind("<MouseWheel>", on_mousewheel)
    items_frame.bind("<MouseWheel>", on_mousewheel)

    def scroll_to_selected():
        if not buttons or selected_idx[0] >= len(buttons):
            return
        btn = buttons[selected_idx[0]]
        items_frame.update_idletasks()
        canvas = items_frame._parent_canvas
        total_h = items_frame._parent_frame.winfo_reqheight()
        if total_h <= 0:
            return
        btn_top, btn_bot = btn.winfo_y(), btn.winfo_y() + btn.winfo_height()
        vis_top, vis_bot = int(canvas.canvasy(0)), int(canvas.canvasy(0)) + canvas.winfo_height()
        if btn_top < vis_top:
            canvas.yview_moveto(max(0.0, btn_top / total_h))
        elif btn_bot > vis_bot:
            canvas.yview_moveto(max(0.0, (btn_bot - canvas.winfo_height()) / total_h))

    def update_highlight():
        for i, btn in enumerate(buttons):
            is_sel = i == selected_idx[0]
            btn.configure(
                fg_color=SELECTED_BG if is_sel else COLOR_PALETTE[i % len(COLOR_PALETTE)],
                text_color=SELECTED_TEXT if is_sel else DEFAULT_TEXT,
            )
        scroll_to_selected()

    def select(idx: int):
        if 0 <= idx < len(items):
            result_app[0] = items[idx]
            root.quit()

    def run_command():
        cmd = search_var.get().strip()
        if cmd:
            result_cmd[0] = cmd
            root.quit()

    def update_list(new_items: list[dict]):
        nonlocal items
        items = new_items
        if selected_idx[0] >= len(items):
            selected_idx[0] = max(0, len(items) - 1)

        for btn in buttons:
            btn.destroy()
        buttons.clear()

        for i, app in enumerate(new_items):
            name = app["name"]
            if app["is_running"]:
                name = f"{name}  (running)"
            if len(name) > MAX_DISPLAY_LEN:
                name = name[: MAX_DISPLAY_LEN - 3] + "..."

            is_sel = i == selected_idx[0]
            btn = ctk.CTkButton(
                items_frame,
                text=name,
                anchor="w",
                font=mono_font,
                height=ITEM_ROW_HEIGHT,
                corner_radius=0,
                fg_color=SELECTED_BG if is_sel else COLOR_PALETTE[i % len(COLOR_PALETTE)],
                hover_color=HOVER_COLOR,
                text_color=SELECTED_TEXT if is_sel else DEFAULT_TEXT,
                command=lambda idx=i: select(idx),
            )
            btn.grid(row=i, column=0, padx=4, pady=1, sticky="ew")
            buttons.append(btn)

    def restore_focus():
        if previous_app:
            time.sleep(0.1)
            previous_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    # Event handlers
    def on_search(*_):
        selected_idx[0] = 0
        update_list(get_app_suggestions(search_var.get()))

    def on_enter(_):
        if items and selected_idx[0] < len(items):
            select(selected_idx[0])
        else:
            run_command()

    def on_up(_):
        if selected_idx[0] > 0:
            selected_idx[0] -= 1
            update_highlight()
        return "break"

    def on_down(_):
        if selected_idx[0] < len(buttons) - 1:
            selected_idx[0] += 1
            update_highlight()
        return "break"

    def on_clear(_):
        search_var.set("")
        return "break"

    def on_delete_word(_):
        entry = search_entry._entry
        cursor, text = entry.index("insert"), search_var.get()
        pos = cursor
        while pos > 0 and text[pos - 1] == " ":
            pos -= 1
        while pos > 0 and text[pos - 1] != " ":
            pos -= 1
        entry.delete(pos, cursor)
        return "break"

    def on_kill_fwd(_):
        search_entry._entry.delete("insert", "end")
        return "break"

    def on_kill_back(_):
        search_entry._entry.delete(0, "insert")
        return "break"

    def on_home(_):
        search_entry._entry.icursor(0)
        return "break"

    def on_end(_):
        search_entry._entry.icursor("end")
        return "break"

    def on_del_char(_):
        search_entry._entry.delete("insert")
        return "break"

    # Keybindings
    search_var.trace_add("write", on_search)
    for key, handler in [
        ("<Return>", on_enter),
        ("<Escape>", lambda _: root.quit()),
        ("<Up>", on_up),
        ("<Down>", on_down),
        ("<Command-BackSpace>", on_clear),
        ("<Option-BackSpace>", on_delete_word),
        ("<Control-w>", on_delete_word),
        ("<Control-u>", on_kill_back),
        ("<Control-k>", on_kill_fwd),
        ("<Control-a>", on_home),
        ("<Control-e>", on_end),
        ("<Control-d>", on_del_char),
        ("<Control-p>", on_up),
        ("<Control-n>", on_down),
    ]:
        search_entry.bind(key, handler)
    root.bind("<Escape>", lambda _: root.quit())

    # Show window
    root.deiconify()
    root.lift()
    root.focus_force()
    search_entry.focus_set()
    root.after(1, lambda: update_list(get_app_suggestions("")))

    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass

    # Handle result
    if result_app[0]:
        app = result_app[0]
        save_app_to_history(app.get("bundle_id") or app["name"])
        if app["is_running"]:
            focus_app(app["app_obj"])
        else:
            launch_app(app["path"])
    elif result_cmd[0]:
        launch_command(result_cmd[0])
        save_command(result_cmd[0])
        restore_focus()
    else:
        restore_focus()


if __name__ == "__main__":
    run_popup()
