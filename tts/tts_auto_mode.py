"""
tts_auto_mode.py — TTS auto-mode normalization.

Adapted from OpenClaw src/tts/tts-auto-mode.ts.

Normalizes TTS auto-mode values across different message sources
and channel conventions into a single canonical enum.

Hermes has no TTS mode normalization — voice_mode.py handles
activation but not message-level TTS directives.
"""

from __future__ import annotations

from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TtsAutoMode(str, Enum):
    """When to automatically generate TTS for messages."""
    OFF = "off"           # Never auto-TTS
    ALWAYS = "always"     # TTS for every response
    INBOUND = "inbound"   # TTS for every inbound message
    TAGGED = "tagged"     # TTS only when [[tts]] tag is present


def normalize_auto_mode(
    value: str | bool | None,
    *,
    accept_off: bool = True,
) -> TtsAutoMode | None:
    """
    Normalize a TTS auto-mode value from various sources.

    Handles booleans, strings, and channel-specific conventions.
    Returns None if the value is invalid and accept_off is True.
    """
    if value is None:
        return TtsAutoMode.OFF if accept_off else None

    if isinstance(value, bool):
        return TtsAutoMode.ALWAYS if value else TtsAutoMode.OFF

    normalized = str(value).strip().lower()

    # Direct matches
    for mode in TtsAutoMode:
        if normalized == mode.value:
            return mode

    # Aliases
    if normalized in ("true", "1", "yes", "on", "all", "every"):
        return TtsAutoMode.ALWAYS
    if normalized in ("false", "0", "no", "none"):
        return TtsAutoMode.OFF
    if normalized in ("inbound_only", "inbound-only", "incoming"):
        return TtsAutoMode.INBOUND
    if normalized in ("tag", "tagged_only", "tagged-only"):
        return TtsAutoMode.TAGGED

    logger.warning(f"Unknown TTS auto-mode: {value!r}")
    return TtsAutoMode.OFF if accept_off else None


def should_tts(mode: TtsAutoMode, has_tts_tag: bool = False) -> bool:
    """
    Determine if TTS should be generated for a message.

    Args:
        mode: Current auto-mode setting
        has_tts_tag: Whether the message contains a [[tts]] directive tag
    """
    if mode == TtsAutoMode.OFF:
        return False
    if mode == TtsAutoMode.ALWAYS:
        return True
    if mode == TtsAutoMode.TAGGED:
        return has_tts_tag
    if mode == TtsAutoMode.INBOUND:
        return True  # Assumes this is called for inbound messages
    return False
