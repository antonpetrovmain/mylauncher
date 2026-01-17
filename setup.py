from setuptools import setup, find_packages

setup(
    name="mycli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rumps",
        "pyobjc-framework-Quartz",
        "pyobjc-framework-Cocoa",
        "desktop-notifier",
        "customtkinter>=5.2.0",
    ],
    entry_points={
        "console_scripts": [
            "mycli=mycli.app:main",
        ],
    },
    python_requires=">=3.14",
    author="User",
    description="macOS Command Launcher with menu bar icon and global hotkey",
)
