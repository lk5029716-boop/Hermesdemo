"""Prompt styling helpers.

Ported from OpenClaw src/terminal/prompt-style.ts

Simple stubs that apply no formatting when color is unavailable.
"""

from __future__ import annotations

from collections.abc import Callable

from .palette import LOBSTER_PALETTE


def _supports_color() -> bool:
    """Basic check for color support."""
    import os
    import sys
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()  # type: ignore[union-attr]


def style_prompt_message(message: str) -> str:
    """Style a prompt message (stub — returns unformatted in plain mode)."""
    if _supports_color():
        return f"\x1b[38;2;255;90;45m{message}\x1b[0m"
    return message


def style_prompt_title(title: str | None) -> str | None:
    """Style a prompt title (stub — returns unformatted in plain mode)."""
    if title and _supports_color():
        return f"\x1b[1;38;2;255;90;45m{title}\x1b[0m"
    return title


def style_prompt_hint(hint: str | None) -> str | None:
    """Style a prompt hint (stub — returns unformatted in plain mode)."""
    if hint and _supports_color():
        return f"\x1b[38;2;139;127;119m{hint}\x1b[0m"
    return hint


def is_rich() -> bool:
    """Check if rich (colored) output is available."""
    return _supports_color()


def colorize(rich: bool, color_fn: "Callable[[str], str]", value: str) -> str:
    """Apply color only if rich output is available."""
    return color_fn(value) if rich else value
