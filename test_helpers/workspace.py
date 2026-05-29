"""Workspace test helpers.

Ported from OpenClaw src/test-helpers/workspace.ts
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


async def make_temp_workspace(prefix: str = "workspace-") -> str:
    """Create a temporary workspace directory."""
    return tempfile.mkdtemp(prefix=prefix)


async def write_workspace_file(
    dir: str,
    name: str,
    content: str,
) -> str:
    """Write a file inside a workspace directory. Returns the file path."""
    file_path = os.path.join(dir, name)
    Path(file_path).write_text(content)
    return file_path
