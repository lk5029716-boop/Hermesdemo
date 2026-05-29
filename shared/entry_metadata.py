"""Emoji and homepage metadata resolution.

Ported from OpenClaw src/shared/entry-metadata.ts
"""

from __future__ import annotations

from .string_coerce import normalize_optional_string


def resolve_emoji_and_homepage(
    metadata: dict | None = None,
    frontmatter: dict | None = None,
) -> dict[str, str]:
    """Resolve emoji and homepage from metadata or frontmatter."""
    emoji = (metadata or {}).get("emoji") or (frontmatter or {}).get("emoji")
    homepage_raw = (
        (metadata or {}).get("homepage")
        or (frontmatter or {}).get("homepage")
        or (frontmatter or {}).get("website")
        or (frontmatter or {}).get("url")
    )
    homepage = normalize_optional_string(homepage_raw)
    result: dict[str, str] = {}
    if emoji:
        result["emoji"] = emoji
    if homepage:
        result["homepage"] = homepage
    return result
