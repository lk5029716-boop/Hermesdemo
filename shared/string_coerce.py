"""Core string coercion utilities.

Ported from OpenClaw src/shared/string-coerce.ts
"""

from __future__ import annotations


def read_string_value(value: object) -> str | None:
    return value if isinstance(value, str) else None


def normalize_nullable_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def normalize_optional_string(value: object) -> str | None:
    result = normalize_nullable_string(value)
    return result if result is not None else None


def normalize_fast_mode(raw: str | bool | None) -> bool | None:
    if isinstance(raw, bool):
        return raw
    if not raw:
        return None
    key = normalize_optional_string(str(raw).lower()) or ""
    if key in {"off", "false", "no", "0", "disable", "disabled", "normal"}:
        return False
    if key in {"on", "true", "yes", "1", "enable", "enabled", "fast"}:
        return True
    return None


def lowercase_preserving_whitespace(value: str) -> str:
    return value.lower()


def resolve_primary_string_value(value: object) -> str | None:
    if isinstance(value, str):
        return normalize_optional_string(value)
    if not value or not isinstance(value, dict):
        return None
    return normalize_optional_string(value.get("primary"))


def has_nonempty_string(value: object) -> bool:
    return normalize_optional_string(value) is not None
