"""
Setup script for building MyLauncher.app using py2app.

Usage:
    python setup_app.py py2app
"""

from setuptools import setup

APP = ["mylauncher/app.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/MyLauncher.icns",
    "plist": {
        "CFBundleName": "MyLauncher",
        "CFBundleDisplayName": "MyLauncher",
        "CFBundleIdentifier": "com.mylauncher.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSMinimumSystemVersion": "10.15",
        "LSUIElement": True,  # Menu bar app (no dock icon)
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "MyLauncher needs to control apps for launching and switching.",
        "NSAccessibilityUsageDescription": "MyLauncher needs accessibility access for global hotkeys.",
    },
    "packages": ["mylauncher", "customtkinter", "rumps"],
    "includes": [
        "AppKit",
        "Cocoa",
        "Quartz",
        "objc",
        "PIL",
    ],
    "excludes": ["tkinter.test", "unittest"],
    "frameworks": [],
}

setup(
    name="MyLauncher",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
