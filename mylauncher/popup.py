"""Standalone popup runner using customtkinter."""

from __future__ import annotations

import multiprocessing
from multiprocessing import Queue
from typing import Any

import customtkinter as ctk

# Lazy imports for faster startup - these are loaded after window is visible
_apps_module = None
_appkit_module = None


def _get_apps_module():
    """Lazy load apps module."""
    global _apps_module
    if _apps_module is None:
        from . import apps as _apps_module
    return _apps_module


def _get_appkit():
    """Lazy load AppKit."""
    global _appkit_module
    if _appkit_module is None:
        import AppKit as _appkit_module
    return _appkit_module


# Config imports are lightweight, keep them
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


def run_popup() -> None:
    """Run the popup window."""
    # Defer AppKit import - capture previous app later
    previous_app = [None]

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
    apps_loaded = [False]

    # Search entry
    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(
        root,
        textvariable=search_var,
        placeholder_text="Switch app, @all apps, >command...",
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

    def close_popup():
        """Hide window immediately and exit mainloop."""
        root.withdraw()
        # Destroy buttons explicitly to prevent Tk cleanup crash
        for btn in buttons:
            try:
                btn.destroy()
            except Exception:
                pass
        buttons.clear()
        # Schedule destroy on next tick to ensure clean exit
        def safe_destroy():
            try:
                root.destroy()
            except Exception:
                pass
        root.after(1, safe_destroy)

    def select(idx: int):
        if 0 <= idx < len(items):
            result_app[0] = items[idx]
            close_popup()

    def run_command():
        cmd = search_var.get().strip()
        if cmd.startswith(">"):
            cmd = cmd[1:].strip()  # Strip ">" prefix
        if cmd:
            result_cmd[0] = cmd
            close_popup()

    def update_list(new_items: list[dict]):
        nonlocal items
        items = new_items
        if selected_idx[0] >= len(items):
            selected_idx[0] = max(0, len(items) - 1)

        for btn in buttons:
            btn.destroy()
        buttons.clear()

        # Command mode: show "Run command" indicator
        text = search_var.get()
        if not new_items and text.startswith(">"):
            cmd = text[1:].strip()
            display = f"⏎ Run: {cmd}" if cmd else "⏎ Run command..."
            if len(display) > MAX_DISPLAY_LEN:
                display = display[: MAX_DISPLAY_LEN - 3] + "..."
            btn = ctk.CTkButton(
                items_frame,
                text=display,
                anchor="w",
                font=mono_font,
                height=ITEM_ROW_HEIGHT,
                corner_radius=0,
                fg_color=COLOR_PALETTE[0],
                hover_color=HOVER_COLOR,
                text_color=DEFAULT_TEXT,
                state="disabled",
            )
            btn.grid(row=0, column=0, padx=4, pady=1, sticky="ew")
            buttons.append(btn)
            return

        for i, app in enumerate(new_items):
            name = app["name"]
            if not app["is_running"]:
                name = f"{name}  (not running)"
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
        import time
        if previous_app[0]:
            time.sleep(0.1)
            AppKit = _get_appkit()
            previous_app[0].activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)

    # Event handlers
    def get_suggestions(text: str) -> list[dict]:
        """Get app suggestions based on search text. Use @ prefix for all apps, > for command mode."""
        if text.startswith(">"):
            return []  # Command mode - disable app list
        if not apps_loaded[0]:
            return []  # Apps not loaded yet
        apps = _get_apps_module()
        if text.startswith("@"):
            return apps.get_all_app_suggestions(text[1:])
        return apps.get_running_app_suggestions(text)

    def on_search(*_):
        selected_idx[0] = 0
        update_list(get_suggestions(search_var.get()))

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
        ("<Escape>", lambda _: close_popup()),
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
    root.bind("<Escape>", lambda _: close_popup())

    # Show window immediately - user can start typing right away
    root.deiconify()
    root.lift()
    root.focus_force()
    search_entry.focus_set()

    def load_apps_async():
        """Load apps and previous app reference in background."""
        # Capture previous app (needs AppKit)
        AppKit = _get_appkit()
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        previous_app[0] = workspace.frontmostApplication()

        # Load apps module and populate list
        apps_loaded[0] = True
        # Only update if user hasn't typed anything yet
        if not search_var.get():
            apps = _get_apps_module()
            update_list(apps.get_running_app_suggestions(""))

    # Schedule heavy loading after window is visible
    root.after(1, load_apps_async)

    try:
        root.mainloop()
    except Exception:
        pass  # Window was destroyed, mainloop exited

    # Handle result
    if result_app[0]:
        app = result_app[0]
        apps = _get_apps_module()
        apps.save_app_to_history(app.get("bundle_id") or app["name"])
        if app["is_running"]:
            apps.focus_app(app["app_obj"])
        else:
            apps.launch_app(app["path"])
    elif result_cmd[0]:
        from .executor import launch_command
        from .history import save_command
        launch_command(result_cmd[0])
        save_command(result_cmd[0])
        restore_focus()
    else:
        restore_focus()


def popup_worker(command_queue: Queue, result_queue: Queue) -> None:
    """
    Worker process that keeps running and waits for show commands.

    This eliminates the ~500ms spawn delay by keeping the process warm.
    The process waits on command_queue for "show" commands, displays
    the popup, and sends results back via result_queue.
    """
    # Initialize Tkinter once - this is the expensive part we're avoiding
    ctk.set_appearance_mode("system")

    # Pre-import heavy modules during startup
    _get_appkit()
    _get_apps_module()

    while True:
        try:
            # Wait for show command
            cmd = command_queue.get()

            if cmd == "quit":
                break

            if cmd == "show":
                # Run the popup and capture any result
                run_popup()
                # Signal completion
                result_queue.put("done")
        except (EOFError, BrokenPipeError):
            # Parent process closed the queue
            break
        except Exception as e:
            # Log error but keep running
            print(f"Popup worker error: {e}")
            result_queue.put("error")


if __name__ == "__main__":
    run_popup()
