"""Temp directory with auto-cleanup.

Ported from OpenClaw src/test-utils/temp-dir.ts
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


async def with_temp_dir(prefix: str, run: Callable[[str], T]) -> T:
    """Create a temp directory, run a function with its path, then clean up."""
    dir_path = tempfile.mkdtemp(prefix=prefix)
    try:
        return run(dir_path)
    finally:
        shutil.rmtree(dir_path, ignore_errors=True)
