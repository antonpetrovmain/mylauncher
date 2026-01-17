"""Command execution logic for MyCLI."""

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExecutionResult:
    """Result of a command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int


def launch_command(command: str) -> None:
    """
    Launch a command without waiting for it to complete.

    Args:
        command: The shell command to launch
    """
    home_dir = Path.home()

    # Source .zshrc to get PATH, then run command
    shell_command = f'source ~/.zshrc 2>/dev/null; {command}'
    subprocess.Popen(
        ["/bin/zsh", "-c", shell_command],
        cwd=home_dir,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def execute_command(command: str, timeout: Optional[int] = 10) -> ExecutionResult:
    """
    Execute a command in the user's home directory.

    Args:
        command: The shell command to execute
        timeout: Maximum seconds to wait (default 10)

    Returns:
        ExecutionResult with success status and output
    """
    home_dir = Path.home()

    process = None
    try:
        # Source .zshrc to get PATH, then run command
        # Using non-interactive shell to avoid hanging on interactive apps
        shell_command = f'source ~/.zshrc 2>/dev/null; {command}'
        process = subprocess.Popen(
            ["/bin/zsh", "-c", shell_command],
            cwd=home_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout)
        return ExecutionResult(
            success=(process.returncode == 0),
            stdout=stdout,
            stderr=stderr,
            return_code=process.returncode,
        )
    except subprocess.TimeoutExpired:
        if process:
            # Kill the entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            return_code=-1,
        )
    except Exception as e:
        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
            except Exception:
                pass
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            return_code=-1,
        )
