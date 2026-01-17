"""Notification wrapper for MyCLI using desktop-notifier."""

import asyncio
import logging

from desktop_notifier import DesktopNotifier

# Suppress desktop-notifier warnings
logging.getLogger("desktop_notifier").setLevel(logging.ERROR)

notifier = DesktopNotifier(app_name="MyCLI")


def _truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    except Exception:
        pass  # Silently fail if notifications aren't available


def notify_success(command: str, output: str) -> None:
    """Send a success notification."""
    title = "Command Succeeded"
    message = f"$ {_truncate(command, 50)}"
    if output.strip():
        message += f"\n{_truncate(output.strip())}"
    _run_async(notifier.send(title=title, message=message))


def notify_failure(command: str, error: str) -> None:
    """Send a failure notification."""
    title = "Command Failed"
    message = f"$ {_truncate(command, 50)}"
    if error.strip():
        message += f"\n{_truncate(error.strip())}"
    _run_async(notifier.send(title=title, message=message))
