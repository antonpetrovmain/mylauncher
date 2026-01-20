# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for MyLauncher."""

import os
import sys
from pathlib import Path

# Get package paths for including assets
import customtkinter
import desktop_notifier
ctk_path = Path(customtkinter.__file__).parent
dn_path = Path(desktop_notifier.__file__).parent

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(ctk_path), 'customtkinter'),
        (str(dn_path), 'desktop_notifier'),
    ],
    hiddenimports=[
        'mylauncher',
        'mylauncher.app',
        'mylauncher.apps',
        'mylauncher.config',
        'mylauncher.executor',
        'mylauncher.history',
        'mylauncher.hotkey',
        'mylauncher.notifier',
        'mylauncher.popup',
        'rumps',
        'customtkinter',
        'PIL',
        'PIL.Image',
        'AppKit',
        'Cocoa',
        'Quartz',
        'objc',
        'Foundation',
        'CoreFoundation',
        'desktop_notifier',
        'desktop_notifier.macos',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MyLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MyLauncher',
)

app = BUNDLE(
    coll,
    name='MyLauncher.app',
    icon='resources/MyLauncher.icns',
    bundle_identifier='com.mylauncher.app',
    info_plist={
        'CFBundleName': 'MyLauncher',
        'CFBundleDisplayName': 'MyLauncher',
        'CFBundleVersion': '0.1.5',
        'CFBundleShortVersionString': '0.1.5',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,  # Menu bar app - no dock icon
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'MyLauncher needs to control apps for launching and switching.',
        'NSAccessibilityUsageDescription': 'MyLauncher needs accessibility access for global hotkeys.',
    },
)
