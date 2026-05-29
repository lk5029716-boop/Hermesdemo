"""String normalization utilities.

Ported from OpenClaw src/shared/string-normalization.ts
"""

from __future__ import annotations

from .string_coerce import normalize_optional_string


def normalize_optional_lowercase_string(value: object) -> str | None:
    result = normalize_optional_string(value)
    return result.lower() if result else None


def normalize_string_entries(list_: list[object] | None) -> list[str]:
    return [
        s for s in (normalize_optional_string(str(e)) or "" for e in (list_ or []))
        if s
    ]


def unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))  # Preserves order


def unique_strings(values: list[str]) -> list[str]:
    return unique_values(values)


def sort_unique_strings(values: list[str]) -> list[str]:
    return sorted(set(values))


def normalize_sorted_unique_string_entries(values: list[object] | None) -> list[str]:
    return sort_unique_strings(unique_strings(normalize_string_entries(values)))


def normalize_optional_trimmed_string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    result = [s for s in (normalize_optional_string(e) for e in value) if s]
    return result if result else None


def normalize_single_or_trimmed_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [s for s in (normalize_optional_string(e) for e in value) if s]
    result = normalize_optional_string(value)
    return [result] if result else []


def normalize_csv_or_loose_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return normalize_string_entries(value)
    if isinstance(value, str):
        return [entry.strip() for entry in value.split(",") if entry.strip()]
    return []
