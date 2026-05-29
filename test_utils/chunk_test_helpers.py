"""Text chunk validation helpers.

Ported from OpenClaw src/test-utils/chunk-test-helpers.ts
"""

from __future__ import annotations


def count_lines(text: str) -> int:
    """Count the number of lines in a text string."""
    return len(text.split("\n"))


def has_balanced_fences(chunk: str) -> bool:
    """Check if a markdown chunk has balanced code fence markers (``` or ~~~).

    Returns True if every opening fence has a matching closing fence.
    """
    open_fence: dict[str, str | int] | None = None
    for line in chunk.split("\n"):
        stripped = line.lstrip()
        # Match code fences: ``` or ~~~ (3+ chars), indented up to 3 spaces
        import re
        match = re.match(r"^( {0,3})(`{3,}|~{3,})(.*)$", stripped)
        if not match:
            continue
        marker = match.group(2)
        if open_fence is None:
            open_fence = {"marker_char": marker[0], "marker_len": len(marker)}
            continue
        if open_fence["marker_char"] == marker[0] and len(marker) >= open_fence["marker_len"]:  # type: ignore[operator]
            open_fence = None

    return open_fence is None
