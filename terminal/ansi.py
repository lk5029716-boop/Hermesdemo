"""ANSI escape sequence utilities.

Ported from OpenClaw src/terminal/ansi.ts
"""

from __future__ import annotations
import re

# Full CSI: ESC [ <params> <final byte>
_ANSI_CSI_PATTERN = r"\x1b\[[\x20-\x3f]*[\x40-\x7e]"
# OSC: ESC ] <payload> ST
_ANSI_OSC_PATTERN = r"\x1b\][^\x07\x1b]*(?:\x1b\\|\x07)"

_ANSI_CSI_REGEX = re.compile(_ANSI_CSI_PATTERN)
_ANSI_OSC_REGEX = re.compile(_ANSI_OSC_PATTERN)


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text."""
    return _ANSI_OSC_REGEX.sub("", _ANSI_CSI_REGEX.sub("", text))


def sanitize_for_log(text: str) -> str:
    """Sanitize a value for safe interpolation in log messages.

    Strips ANSI escapes, C0/C1 control characters, and DEL to prevent
    log forging / terminal escape injection (CWE-117).
    """
    stripped = strip_ansi(text)
    # Remove control characters (C0: 0x00-0x1f, DEL: 0x7f, C1: 0x80-0x9f)
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", stripped)


# Unicode code point ranges for zero-width characters
_ZERO_WIDTH_RANGES = [
    (0x0300, 0x036F),
    (0x1AB0, 0x1AFF),
    (0x1DC0, 0x1DFF),
    (0x20D0, 0x20FF),
    (0xFE20, 0xFE2F),
    (0xFE00, 0xFE0F),
]
_ZERO_WIDTH_SINGLE = {0x200D}  # ZWJ


def _is_zero_width(code_point: int) -> bool:
    if code_point in _ZERO_WIDTH_SINGLE:
        return True
    return any(start <= code_point <= end for start, end in _ZERO_WIDTH_RANGES)


def _is_full_width(code_point: int) -> bool:
    if code_point < 0x1100:
        return False
    return (
        code_point <= 0x115F
        or code_point in (0x2329, 0x232A)
        or (0x2E80 <= code_point <= 0x3247 and code_point != 0x303F)
        or (0x3250 <= code_point <= 0x4DBF)
        or (0x4E00 <= code_point <= 0xA4C6)
        or (0xA960 <= code_point <= 0xA97C)
        or (0xAC00 <= code_point <= 0xD7A3)
        or (0xF900 <= code_point <= 0xFAFF)
        or (0xFE10 <= code_point <= 0xFE19)
        or (0xFE30 <= code_point <= 0xFE6B)
        or (0xFF01 <= code_point <= 0xFF60)
        or (0xFFE0 <= code_point <= 0xFFE6)
        or (0x1AFF0 <= code_point <= 0x1AFF3)
        or (0x1AFF5 <= code_point <= 0x1AFFB)
        or (0x1AFFD <= code_point <= 0x1AFFE)
        or (0x1B000 <= code_point <= 0x1B2FF)
        or (0x1F200 <= code_point <= 0x1F251)
        or (0x20000 <= code_point <= 0x3FFFD)
    )


_EMOJI_PATTERN = re.compile(r"[\U0001F000-\U0001FFFF\u20E3\uFE0F]", re.UNICODE)


def _grapheme_width(grapheme: str) -> int:
    if not grapheme:
        return 0
    if _EMOJI_PATTERN.search(grapheme):
        return 2

    saw_printable = False
    for char in grapheme:
        cp = ord(char)
        if _is_zero_width(cp):
            continue
        if _is_full_width(cp):
            return 2
        saw_printable = True
    return 1 if saw_printable else 0


def _split_graphemes(text: str) -> list[str]:
    """Split text into grapheme clusters.

    Uses unicodedata for basic combining character support.
    A full port would use the regex crate or ICU.
    """
    if not text:
        return []
    # Basic implementation: iterate and group combining characters
    result: list[str] = []
    current = ""
    import unicodedata
    for char in text:
        cat = unicodedata.category(char)
        if cat.startswith(("M", "S")) and current:
            current += char
        else:
            if current:
                result.append(current)
            current = char
    if current:
        result.append(current)
    return result


def visible_width(text: str) -> int:
    """Compute the visible display width of a string (accounting for wide CJK chars and ANSI escapes)."""
    return sum(_grapheme_width(g) for g in _split_graphemes(strip_ansi(text)))
