"""Regex escape utility.

Ported from OpenClaw src/shared/regexp.ts
"""

from __future__ import annotations

import re


def escape_regexp(value: str) -> str:
    """Escape special regex characters in a string."""
    return re.escape(value)
