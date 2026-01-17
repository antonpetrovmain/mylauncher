"""Command execution logic for MyCLI."""

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


def execute_command(command: str, timeout: Optional[int] = 30) -> ExecutionResult:
    """
    Execute a command in the user's home directory.

    Args:
        command: The shell command to execute
        timeout: Maximum seconds to wait (default 30)

    Returns:
        ExecutionResult with success status and output
    """
    home_dir = Path.home()

    try:
        # Run through interactive login shell to get user's PATH from .zshrc
        result = subprocess.run(
            ["/bin/zsh", "-i", "-l", "-c", command],
            cwd=home_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            return_code=-1,
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            return_code=-1,
        )
