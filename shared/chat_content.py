"""Chat content extraction utilities.

Ported from OpenClaw src/shared/chat-content.ts
"""

from __future__ import annotations

import json
from typing import Callable


def coerce_chat_content_text(value: object) -> str:
    """Coerce any value to a chat-safe text string."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value) or ""
        except (TypeError, ValueError):
            return ""
    return ""


def extract_text_from_chat_content(
    content: object,
    sanitize_text: "Callable[[str], str] | None" = None,
    join_with: str = " ",
    normalize_text: "Callable[[str], str] | None" = None,
) -> str | None:
    """Extract text from chat content (string or list of content blocks)."""
    normalize = normalize_text or (lambda t: " ".join(t.split()))

    def sanitize(text: object) -> str:
        raw = coerce_chat_content_text(text)
        result = sanitize_text(raw) if sanitize_text else raw
        return coerce_chat_content_text(result)

    if isinstance(content, str):
        value = sanitize(content)
        normalized = normalize(value)
        return normalized if normalized else None

    if not isinstance(content, list):
        return None

    chunks: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "text":
            continue
        text = block.get("text")
        value = sanitize(text)
        if value.strip():
            chunks.append(value)

    joined = normalize(join_with.join(chunks))
    return joined if joined else None
