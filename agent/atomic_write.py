"""
Atomic file write utility for Hermes.

Writes to a temp file first, then renames into place.
Prevents corrupted files if the process crashes mid-write.

Based on OpenHands file_store/local.py atomic write pattern.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def atomic_write(path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """Write content to path atomically.

    Writes to a temp file in the same directory, then renames into place.
    If the process crashes mid-write, the original file is preserved.

    Args:
        path: Target file path.
        content: String content to write.
        encoding: Text encoding (default: utf-8).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Temp file in same directory so rename is atomic (same filesystem)
    tmp_fd = None
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=f".{path.name}.tmp.",
        )
        os.write(tmp_fd, content.encode(encoding))
        os.fsync(tmp_fd)
        os.close(tmp_fd)
        tmp_fd = None
        os.replace(tmp_path, path)
        logger.debug("atomic_write: wrote %s (%d bytes)", path, len(content))
    except Exception:
        # Clean up temp file on failure
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except Exception:
                pass
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise


def atomic_write_bytes(path: Union[str, Path], data: bytes) -> None:
    """Write bytes to path atomically. Same as atomic_write but for binary data."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd = None
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=f".{path.name}.tmp.",
        )
        os.write(tmp_fd, data)
        os.fsync(tmp_fd)
        os.close(tmp_fd)
        tmp_fd = None
        os.replace(tmp_path, path)
    except Exception:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except Exception:
                pass
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise
