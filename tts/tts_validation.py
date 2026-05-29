"""
tts_validation.py — TTS provider validation helpers.

Adapted from OpenClaw src/tts/tts-provider-helpers.ts.

Validates TTS provider options: trimming whitespace, enforcing
bounds, sanitizing language codes. Prevents provider errors from
bad input.

Hermes has no centralized TTS validation — each provider module
handles validation independently.
"""

from __future__ import annotations

import re
from typing import Any


def is_empty_whitespace(text: str | None) -> bool:
    """Check if text is empty or only whitespace."""
    return text is None or text.strip() == ""


def trim_to_lines(text: str, max_lines: int | None = None) -> str:
    """Trim text to maximum number of lines."""
    if not text:
        return ""
    lines = text.split("\n")
    if max_lines is not None:
        lines = lines[:max_lines]
    return "\n".join(lines).strip()


def bounded_int(
    value: Any,
    *,
    default: int | None = None,
    min_val: int | None = None,
    max_val: int | None = None,
) -> int | None:
    """Clamp an integer value to a range, returning default if invalid."""
    try:
        num = int(value)
    except (TypeError, ValueError):
        return default

    if min_val is not None and num < min_val:
        num = min_val
    if max_val is not None and num > max_val:
        num = max_val
    return num


def bounded_float(
    value: Any,
    *,
    default: float | None = None,
    min_val: float | None = None,
    max_val: float | None = None,
) -> float | None:
    """Clamp a float value to a range, returning default if invalid."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default

    if min_val is not None and num < min_val:
        num = min_val
    if max_val is not None and num > max_val:
        num = max_val
    return num


def bounded_value_from_ranges(
    value: Any,
    ranges: list[tuple[float, float, Any]],
    default: Any = None,
) -> Any:
    """
    Map a numeric value to a result based on ordered ranges.
    Ranges are (min, max, result). Returns default if no range matches.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default

    for min_v, max_v, result in ranges:
        if min_v <= num < max_v:
            return result

    return default


def normalize_language(text: str | None, *, allowed: list[str] | None = None) -> str | None:
    """
    Normalize a BCP-47 language tag (e.g., "en-US" → "en-US").
    Returns None if not a valid language/region pattern.
    Optionally checks against an allowlist.
    """
    if not text:
        return None

    # Remove duplicates (some UIs send "en,en")
    parts = [p.strip() for p in text.split(",")]
    filtered = []
    seen = set()
    for part in parts:
        if part not in seen:
            seen.add(part)
            filtered.append(part)
    deduped = ",".join(filtered)

    # Validate format: primary language is 2-3 alphabetic chars,
    # region subtag is 2-3 alphanumeric
    if not re.match(r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,3})?$", deduped):
        return None

    # If allowed list provided, return the matching entry or None
    if is_empty_whitespace(deduped) or deduped.lower() == "und":
        return None
    if allowed is not None:
        lowered = deduped.lower()
        for lang_code in allowed:
            if lowered == lang_code.lower():
                return lang_code  # Return the canonical casing from the allowlist
        return None

    return deduped


def validate_seed(seed: str | None) -> str | None:
    """
    Validate and normalize a seed string.
    Seeds must be non-empty and <= 1024 chars.
    """
    if not seed:
        return None
    seed = seed.strip()
    if len(seed) > 0:
        return seed[:1024]
    return None


def cleanup_text_for_tts(text: str) -> str:
    """
    Clean up text before sending to TTS.
    Removes excessive whitespace and normalizes line breaks.
    """
    if not text:
        return ""

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)
    # Collapse multiple newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    return text.strip()
