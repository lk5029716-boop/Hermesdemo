"""Status label formatting helpers.

Ported from OpenClaw src/status/status-labels.ts
"""

from __future__ import annotations


def format_fast_mode_label(enabled: bool) -> str:
    """Format a fast mode indicator label."""
    return f"Fast: {'on' if enabled else 'off'}"
