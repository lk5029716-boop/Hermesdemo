"""
cjk_chars.py — CJK character detection and token estimation.

Adapted from OpenClaw src/utils/cjk-chars.ts.

Detects CJK (Chinese, Japanese, Korean) characters in text and
provides CJK-aware token count estimates.
"""

from __future__ import annotations

import re

# Unicode ranges for CJK characters
CJK_RANGES = [
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0x3400, 0x4DBF),   # CJK Extension A
    (0x20000, 0x2A6DF), # CJK Extension B
    (0x2A700, 0x2B73F), # CJK Extension C
    (0x2B740, 0x2B81F), # CJK Extension D
    (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
    (0x3000, 0x303F),   # CJK Symbols and Punctuation
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
    (0xAC00, 0xD7AF),   # Hangul Syllables
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x3130, 0x318F),   # Hangul Compatibility Jamo
]

# Pre-compiled regex for CJK detection
_CJK_REGEX = re.compile(
    "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in CJK_RANGES) + "]"
)


def is_cjk_char(ch: str) -> bool:
    """Check if a single character is CJK."""
    if len(ch) != 1:
        return False
    code = ord(ch)
    return any(lo <= code <= hi for lo, hi in CJK_RANGES)


def has_cjk(text: str) -> bool:
    """Check if text contains any CJK characters."""
    if not text:
        return False
    return bool(_CJK_REGEX.search(text))


def count_cjk_chars(text: str) -> int:
    """Count CJK characters in text."""
    if not text:
        return 0
    return sum(1 for ch in text if is_cjk_char(ch))


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for mixed-language text.
    CJK: ~1.5 chars/token, Non-CJK: ~4 chars/token.
    """
    if not text:
        return 0
    cjk_count = count_cjk_chars(text)
    non_cjk_count = len(text) - cjk_count
    cjk_tokens = max(1, cjk_count * 2 // 3) if cjk_count else 0
    non_cjk_tokens = max(1, non_cjk_count // 4) if non_cjk_count else 0
    return cjk_tokens + non_cjk_tokens


def split_cjk_aware(text: str, max_chars: int = 512) -> list:
    """Split text into chunks, preferring word boundaries."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks = []
    current = []
    current_len = 0
    for word in text.split(" "):
        word_len = len(word) + 1
        if current_len + word_len > max_chars and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = word_len
        else:
            current.append(word)
            current_len += word_len
    if current:
        chunks.append(" ".join(current))
    return chunks
