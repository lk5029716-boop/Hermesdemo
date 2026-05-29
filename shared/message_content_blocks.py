"""Message content block visitor.

Ported from OpenClaw src/shared/message-content-blocks.ts
"""

from __future__ import annotations

from typing import Callable


def visit_object_content_blocks(
    message: object,
    visitor: Callable[[dict], None],
) -> None:
    """Visit content blocks in a message object."""
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict):
            visitor(block)
