"""Terminal text sanitization.

Ported from OpenClaw src/terminal/safe-text.ts
"""

from __future__ import annotations

from .ansi import strip_ansi


def sanitize_terminal_text(text: str) -> str:
    """Normalize untrusted text for single-line terminal/log rendering.

    Strips ANSI escapes and control characters, escapes whitespace.
    """
    normalized = strip_ansi(text)
    result: list[str] = []
    for char in normalized:
        code = ord(char)
        is_control = (0x00 <= code <= 0x1F) or (0x7F <= code <= 0x9F)
        if not is_control:
            result.append(char)
    return "".join(result)
