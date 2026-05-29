"""Progress line management for terminal output.

Ported from OpenClaw src/terminal/progress-line.ts
"""

from __future__ import annotations

import sys


_active_stream: object | None = None


def register_active_progress_line(stream: object) -> None:
    """Register a stream as the active progress line target."""
    global _active_stream
    # Check for isTTY attribute
    if not getattr(stream, "isatty", lambda: False)():
        return
    _active_stream = stream


def clear_active_progress_line() -> None:
    """Clear the active progress line with ANSI escape."""
    global _active_stream
    if _active_stream is None:
        return
    if not getattr(_active_stream, "isatty", lambda: False)():
        _active_stream = None
        return
    try:
        _active_stream.write("\r\x1b[2K")  # type: ignore[union-attr]
        _active_stream.flush()  # type: ignore[union-attr]
    except (OSError, ValueError):
        _active_stream = None


def unregister_active_progress_line(stream: object | None = None) -> None:
    """Unregister the active progress line stream."""
    global _active_stream
    if _active_stream is None:
        return
    if stream is not None and _active_stream is not stream:
        return
    _active_stream = None
