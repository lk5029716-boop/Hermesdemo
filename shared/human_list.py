"""Human-readable list formatting.

Ported from OpenClaw src/shared/human-list.ts
"""

from __future__ import annotations


def format_human_list(values: list[str]) -> str:
    """Format a list of strings as a human-readable comma-separated list with 'or'."""
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} or {values[1]}"
    return ", ".join(values[:-1]) + f", or {values[-1]}"
