#!/usr/bin/env python3
"""Test script to debug hotkey detection."""

import Quartz

KEY_D = 2
MOD_CMD = Quartz.kCGEventFlagMaskCommand
MOD_CTRL = Quartz.kCGEventFlagMaskControl

def callback(proxy, event_type, event, refcon):
    if event_type == Quartz.kCGEventKeyDown:
        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        flags = Quartz.CGEventGetFlags(event)
        has_cmd = bool(flags & MOD_CMD)
        has_ctrl = bool(flags & MOD_CTRL)
        print(f"Key: keycode={keycode}, cmd={has_cmd}, ctrl={has_ctrl}")
        if keycode == KEY_D and has_cmd and has_ctrl:
            print(">>> Alt+Tab detected! <<<")
    return event

tap = Quartz.CGEventTapCreate(
    Quartz.kCGSessionEventTap,
    Quartz.kCGHeadInsertEventTap,
    Quartz.kCGEventTapOptionDefault,
    Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown),
    callback,
    None,
)

if tap is None:
    print("ERROR: Failed to create event tap!")
    print("Please grant Accessibility permissions:")
    print("  System Settings > Privacy & Security > Accessibility")
else:
    print("Event tap created. Press keys to see their codes.")
    print("Try pressing Alt+Tab. Press Ctrl+C to exit.\n")
    source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), source, Quartz.kCFRunLoopCommonModes)
    Quartz.CGEventTapEnable(tap, True)
    try:
        Quartz.CFRunLoopRun()
    except KeyboardInterrupt:
        print("\nDone")
