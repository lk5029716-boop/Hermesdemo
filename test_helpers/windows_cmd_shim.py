"""Windows cmd shim fixture helper.

Ported from OpenClaw src/test-helpers/windows-cmd-shim.ts
"""

from __future__ import annotations

import os
from pathlib import Path


async def create_windows_cmd_shim_fixture(
    shim_path: str,
    script_path: str,
    shim_line: str,
) -> None:
    """Create a Windows .cmd shim file for testing.

    Args:
        shim_path: Path where the .cmd shim will be written
        script_path: Path where the target script will be written
        shim_line: The command line in the shim (e.g. "node script.js")
    """
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    os.makedirs(os.path.dirname(shim_path), exist_ok=True)
    Path(script_path).write_text("module.exports = {};\n")
    Path(shim_path).write_text(f"@echo off\r\n{shim_line}\r\n")
