"""OSC-8 terminal hyperlink formatting.

Ported from OpenClaw src/terminal/terminal-link.ts
"""

from __future__ import annotations

import sys


def format_terminal_link(
    label: str,
    url: str,
    fallback: str | None = None,
    force: bool | None = None,
) -> str:
    """Format an OSC-8 hyperlink for terminal display.

    Falls back to plain text when not on a TTY.
    """
    safe_label = label.replace("\x1b", "")
    safe_url = url.replace("\x1b", "")

    allow = force if force is not None else hasattr(sys.stdout, "isatty") and sys.stdout.isatty()  # type: ignore[union-attr]
    if not allow:
        return fallback or f"{safe_label} ({safe_url})"

    return f"\x1b]8;;{safe_url}\x07{safe_label}\x1b]8;;\x07"
