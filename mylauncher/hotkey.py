"""Global hotkey registration using CGEventTap for macOS."""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import threading
from typing import Callable, Optional

import Quartz
from PyObjCTools import AppHelper

from . import config

log = logging.getLogger(__name__)

# Special keys that have fixed VK codes (not affected by keyboard layout)
SPECIAL_KEYS = {
    "tab": 48,
    "space": 49,
    "return": 36,
    "enter": 36,
    "escape": 53,
    "esc": 53,
    "delete": 51,
    "backspace": 51,
    "up": 126,
    "down": 125,
    "left": 123,
    "right": 124,
    "f1": 122,
    "f2": 120,
    "f3": 99,
    "f4": 118,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f8": 100,
    "f9": 101,
    "f10": 109,
    "f11": 103,
    "f12": 111,
}


def _parse_modifiers(modifier_str: str) -> int:
    """Parse modifier string like 'cmd+ctrl' into Quartz flag mask."""
    modifiers = {m.strip().lower() for m in modifier_str.split('+')}

    flag = 0
    if 'cmd' in modifiers:
        flag |= Quartz.kCGEventFlagMaskCommand
    if 'ctrl' in modifiers:
        flag |= Quartz.kCGEventFlagMaskControl
    if 'alt' in modifiers:
        flag |= Quartz.kCGEventFlagMaskAlternate
    if 'shift' in modifiers:
        flag |= Quartz.kCGEventFlagMaskShift

    return flag


def _build_vk_to_char_map() -> dict[int, str]:
    """Build a mapping of VK codes to characters using the current keyboard layout."""
    vk_to_char = {}
    try:
        # Load Carbon framework for UCKeyTranslate
        carbon_path = ctypes.util.find_library('Carbon')
        if not carbon_path:
            return vk_to_char
        carbon = ctypes.CDLL(carbon_path)

        # Get current keyboard layout
        kTISPropertyUnicodeKeyLayoutData = ctypes.c_void_p.in_dll(
            carbon, 'kTISPropertyUnicodeKeyLayoutData'
        )
        TISCopyCurrentKeyboardInputSource = carbon.TISCopyCurrentKeyboardInputSource
        TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
        TISGetInputSourceProperty = carbon.TISGetInputSourceProperty
        TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        TISGetInputSourceProperty.restype = ctypes.c_void_p

        source = TISCopyCurrentKeyboardInputSource()
        if not source:
            return vk_to_char

        layout_data = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData)
        if not layout_data:
            return vk_to_char

        # Get the actual data pointer from CFData
        CFDataGetBytePtr = carbon.CFDataGetBytePtr
        CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
        CFDataGetBytePtr.restype = ctypes.c_void_p
        layout_ptr = CFDataGetBytePtr(layout_data)
        if not layout_ptr:
            return vk_to_char

        # UCKeyTranslate function
        UCKeyTranslate = carbon.UCKeyTranslate
        UCKeyTranslate.argtypes = [
            ctypes.c_void_p,  # keyLayoutPtr
            ctypes.c_uint16,  # virtualKeyCode
            ctypes.c_uint16,  # keyAction
            ctypes.c_uint32,  # modifierKeyState
            ctypes.c_uint32,  # keyboardType
            ctypes.c_uint32,  # keyTranslateOptions
            ctypes.POINTER(ctypes.c_uint32),  # deadKeyState
            ctypes.c_uint8,   # maxStringLength
            ctypes.POINTER(ctypes.c_uint8),   # actualStringLength
            ctypes.c_void_p,  # unicodeString
        ]
        UCKeyTranslate.restype = ctypes.c_int32

        kUCKeyActionDown = 0
        kUCKeyTranslateNoDeadKeysBit = 0

        # Try all VK codes 0-50 (covers most letter keys)
        for vk in range(51):
            dead_key_state = ctypes.c_uint32(0)
            actual_length = ctypes.c_uint8(0)
            unicode_string = (ctypes.c_uint16 * 4)()

            result = UCKeyTranslate(
                layout_ptr,
                ctypes.c_uint16(vk),
                ctypes.c_uint16(kUCKeyActionDown),
                ctypes.c_uint32(0),  # No modifiers
                ctypes.c_uint32(0),  # LMGetKbdType() - 0 works for current
                ctypes.c_uint32(kUCKeyTranslateNoDeadKeysBit),
                ctypes.byref(dead_key_state),
                ctypes.c_uint8(4),
                ctypes.byref(actual_length),
                unicode_string,
            )

            if result == 0 and actual_length.value == 1:
                char = chr(unicode_string[0]).lower()
                if char.isalpha():
                    vk_to_char[vk] = char

        log.debug(f"Built VK->char map with {len(vk_to_char)} entries")
    except Exception as e:
        log.warning(f"Failed to build VK->char map: {e}")

    return vk_to_char


class HotkeyManager:
    """Manages global hotkey registration using CGEventTap to capture and consume events."""

    def __init__(self, on_hotkey: Callable[[], None]):
        self._on_hotkey = on_hotkey
        self._tap = None
        self._run_loop_source = None
        self._thread: threading.Thread | None = None
        self._running = False

        # Parse configured modifiers
        self._mod_flags = _parse_modifiers(config.HOTKEY_MODIFIERS)

        # Get VK code for configured key
        key_name = config.HOTKEY_KEY.lower()

        # First check special keys (tab, space, return, etc.)
        if key_name in SPECIAL_KEYS:
            self._hotkey_vk = SPECIAL_KEYS[key_name]
            log.info(f"Hotkey configured: {config.HOTKEY_MODIFIERS}+{config.HOTKEY_KEY} (VK={self._hotkey_vk}, special key)")
        else:
            # Build VK -> char mapping for letter keys using keyboard layout
            self._vk_to_char = _build_vk_to_char_map()
            char_to_vk = {v: k for k, v in self._vk_to_char.items()}
            self._hotkey_vk = char_to_vk.get(key_name)

            if self._hotkey_vk is not None:
                log.info(f"Hotkey configured: {config.HOTKEY_MODIFIERS}+{config.HOTKEY_KEY} (VK={self._hotkey_vk})")
            else:
                log.warning(f"Could not find VK code for key '{config.HOTKEY_KEY}', using fallback VK=2 (D)")
                self._hotkey_vk = 2  # Fallback to 'D' on US keyboard

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

                # Check if all required modifiers are pressed and the hotkey key matches
                has_required_mods = (flags & self._mod_flags) == self._mod_flags

                if keycode == self._hotkey_vk and has_required_mods:
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
    Register a callback function for the global hotkey.

    The hotkey is configured in ~/.config/mylauncher/config.toml
    Default: Cmd+Ctrl+D

    Args:
        callback: Function to call when hotkey is pressed
    """
    global _manager
    _manager = HotkeyManager(callback)
    _manager.start()
