from setuptools import setup, find_packages

setup(
    name="mylauncher",
    version="0.1.7",
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
            "mylauncher=mylauncher.app:main",
        ],
    },
    python_requires=">=3.14",
    author="User",
    description="macOS app launcher with menu bar icon and global hotkey",
)
