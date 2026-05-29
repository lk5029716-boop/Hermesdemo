"""Record/dict coercion utilities.

Ported from OpenClaw src/shared/record-coerce.ts
"""

from __future__ import annotations


def is_record(value: object) -> bool:
    """Check if a value is a plain dict (not list, not None)."""
    return isinstance(value, dict)


def read_string_field(record: dict | None, key: str) -> str | None:
    if not record:
        return None
    value = record.get(key)
    return value if isinstance(value, str) else None


def as_optional_record(value: object) -> dict | None:
    return value if isinstance(value, dict) else None


def as_nullable_record(value: object) -> dict | None:
    return value if isinstance(value, dict) else None
