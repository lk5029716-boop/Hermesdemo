"""
directive_tags.py — Inline directive parsing for messages.

Adapted from OpenClaw src/utils/directive-tags.ts.

Parses inline directives like [[reply_to_current]], [[audio_as_voice]],
[[model:gpt-4o]] from message text.

Useful for: message formatting hints, model override directives,
delivery instructions embedded in content.

Hermes processes messages through the agent loop; directives
can control how messages are handled without separate API calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Pattern: [[directive_name]] or [[directive_name:value]]
DIRECTIVE_PATTERN = re.compile(r"\[\[([a-zA-Z_][a-zA-Z0-9_-]*)(?::([^\[\]]+))?\]\]")


class DirectiveType(str, Enum):
    REPLY_TO_CURRENT = "reply_to_current"
    REPLY_TO_ORIGINAL = "reply_to_original"
    AUDIO_AS_VOICE = "audio_as_voice"
    MODEL = "model"
    THINKING = "thinking"
    VERBOSE = "verbose"
    ACTIVATION = "activation"
    HINT = "hint"
    SPONSORED_BY = "sponsored_by"
    RESOLUTION_NOTES = "resolution_notes"


from enum import Enum


@dataclass
class ParsedDirective:
    """A parsed inline directive."""
    raw: str
    type: str
    value: str | None = None
    position: int = 0


@dataclass
class DirectiveParseResult:
    """Result of parsing directives from text."""
    text: str                      # Text with directives removed
    directives: list[ParsedDirective]  # Extracted directives


def parse_directives(text: str | None, remove: bool = True) -> DirectiveParseResult:
    """
    Parse inline directives from message text.

    Args:
        text: Message text that may contain [[directive]] tags
        remove: If True, strip directives from returned text

    Returns:
        DirectiveParseResult with cleaned text and extracted directives

    Example:
        >>> result = parse_directives("Hello [[reply_to_current]] world")
        >>> result.text
        'Hello  world'
        >>> result.directives[0].type
        'reply_to_current'
    """
    if not text:
        return DirectiveParseResult(text="", directives=[])

    directives: list[ParsedDirective] = []

    for match in DIRECTIVE_PATTERN.finditer(text):
        directive_type = match.group(1) or ""
        directive_value = match.group(2)
        directives.append(ParsedDirective(
            raw=match.group(0),
            type=directive_type,
            value=directive_value if directive_value else None,
            position=match.start(),
        ))

    cleaned = text
    if remove:
        cleaned = DIRECTIVE_PATTERN.sub("", text)
        # Clean up double spaces left by removal
        cleaned = re.sub(r"  +", " ", cleaned).strip()

    return DirectiveParseResult(text=cleaned, directives=directives)


def has_directive(text: str | None, directive_type: str) -> bool:
    """Check if text contains a specific directive type."""
    if not text:
        return False
    result = parse_directives(text, remove=False)
    return any(d.type == directive_type for d in result.directives)


def get_directive_value(text: str | None, directive_type: str) -> str | None:
    """Get the value of the first matching directive."""
    if not text:
        return None
    result = parse_directives(text, remove=False)
    for d in result.directives:
        if d.type == directive_type:
            return d.value
    return None


def strip_directives(text: str | None) -> str:
    """Remove all directives from text."""
    if not text:
        return ""
    return DIRECTIVE_PATTERN.sub("", text).strip()


def is_known_directive(directive_type: str) -> bool:
    """Check if a directive type is in the known set."""
    try:
        DirectiveType(directive_type)
        return True
    except ValueError:
        return False
