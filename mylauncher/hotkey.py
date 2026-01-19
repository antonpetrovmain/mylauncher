"""Global hotkey registration using CGEventTap for macOS."""

from __future__ import annotations

import threading
from typing import Callable, Optional

import Quartz
from PyObjCTools import AppHelper


class HotkeyManager:
    """Manages global hotkey registration using CGEventTap to capture and consume events."""

    # Key codes (macOS virtual key codes)
    KEY_D = 5

    # Modifier flags
    MOD_CMD = Quartz.kCGEventFlagMaskCommand
    MOD_CTRL = Quartz.kCGEventFlagMaskControl

    def __init__(self, on_hotkey: Callable[[], None]):
        self._on_hotkey = on_hotkey
        self._tap = None
        self._run_loop_source = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """Start listening for global hotkeys."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_event_tap, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop listening for global hotkeys."""
        self._running = False
        if self._tap:
            Quartz.CGEventTapEnable(self._tap, False)
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run_event_tap(self) -> None:
        """Run the event tap in a background thread."""
        # Create callback
        def callback(proxy, event_type, event, refcon):
            if event_type == Quartz.kCGEventKeyDown:
                keycode = Quartz.CGEventGetIntegerValueField(
                    event, Quartz.kCGKeyboardEventKeycode
                )
                flags = Quartz.CGEventGetFlags(event)

                # Check for Cmd+Ctrl+D
                has_cmd = bool(flags & self.MOD_CMD)
                has_ctrl = bool(flags & self.MOD_CTRL)

                if keycode == self.KEY_D and has_cmd and has_ctrl:
                    # Trigger callback on main thread (required for UI operations)
                    AppHelper.callAfter(self._on_hotkey)
                    # Return None to consume the event (prevent it from reaching other apps)
                    return None

            return event

        # Create event tap
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown),
            callback,
            None,
        )

        if self._tap is None:
            print("ERROR: Failed to create event tap!")
            print("Please grant Accessibility permissions:")
            print("  System Settings > Privacy & Security > Accessibility")
            print("  Add and enable your terminal app or Python")
            return

        # Create run loop source
        self._run_loop_source = Quartz.CFMachPortCreateRunLoopSource(
            None, self._tap, 0
        )

        # Add to run loop
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            self._run_loop_source,
            Quartz.kCFRunLoopCommonModes,
        )

        # Enable the tap
        Quartz.CGEventTapEnable(self._tap, True)

        # Run the loop (0.1s timeout for better stop() responsiveness)
        while self._running:
            Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 0.1, False)


_manager: Optional[HotkeyManager] = None


def register_hotkey(callback: Callable[[], None]) -> None:
    """
    Register a callback function for the global hotkey (Cmd+Ctrl+D).

    Args:
        callback: Function to call when hotkey is pressed
    """
    global _manager
    _manager = HotkeyManager(callback)
    _manager.start()
