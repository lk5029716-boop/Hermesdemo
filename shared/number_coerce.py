"""Number coercion utilities.

Ported from OpenClaw src/shared/number-coercion.ts
"""

from __future__ import annotations
import re

_FINITE_RE = re.compile(r'^[+-]?(?:(?:\d+\.?\d*)|(?:\.\d+))(?:e[+-]?\d+)?$', re.IGNORECASE)


def as_finite_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return value if value == value and abs(value) != float('inf') else None  # NaN check
    return None


def as_safe_integer_in_range(value: object, min_val: int | None = None, max_val: int | None = None) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    if min_val is not None and value < min_val:
        return None
    if max_val is not None and value > max_val:
        return None
    return value


def parse_finite_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return value if value == value and abs(value) != float('inf') else None
    if isinstance(value, str):
        trimmed = value.strip()
        if trimmed and _FINITE_RE.match(trimmed):
            parsed = float(trimmed)
            return parsed if parsed == parsed and abs(parsed) != float('inf') else None
    return None


def as_positive_safe_integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None
