"""Balanced JSON extraction utility.

Ported from OpenClaw src/shared/balanced-json.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BalancedJsonFragment:
    json: str
    start_index: int
    end_index: int


CLOSING_DELIMITER = {"{": "}", "[": "]"}


def extract_balanced_json_prefix(raw: str) -> BalancedJsonFragment | None:
    """Extract a balanced JSON object/array prefix from a string."""
    start = 0
    while start < len(raw) and raw[start] not in CLOSING_DELIMITER:
        start += 1
    if start >= len(raw):
        return None

    stack: list[str] = []
    in_string = False
    escaped = False
    for i in range(start, len(raw)):
        char = raw[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in CLOSING_DELIMITER:
            stack.append(char)
            continue
        opener = stack[-1] if stack else None
        if opener and char == CLOSING_DELIMITER.get(opener, ""):
            stack.pop()
            if not stack:
                return BalancedJsonFragment(
                    json=raw[start:i+1],
                    start_index=start,
                    end_index=i,
                )
    return None


def extract_balanced_json_fragments(raw: str) -> list[BalancedJsonFragment]:
    """Extract all balanced JSON fragments from a string."""
    fragments: list[BalancedJsonFragment] = []
    offset = 0
    while offset < len(raw):
        fragment = extract_balanced_json_prefix(raw[offset:])
        if fragment is None:
            break
        fragments.append(BalancedJsonFragment(
            json=fragment.json,
            start_index=offset + fragment.start_index,
            end_index=offset + fragment.end_index,
        ))
        offset += fragment.end_index + 1
    return fragments
