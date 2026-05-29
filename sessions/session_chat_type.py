"""Session chat type derivation from session keys.

Ported from OpenClaw src/sessions/session-chat-type-shared.ts
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class SessionChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


def derive_session_chat_type_from_scoped_key(
    scoped_session_key: str,
    derive_legacy: list[Callable[[str], SessionChatType | None]] | None = None,
) -> SessionChatType:
    """Best-effort chat-type extraction from a scoped session key.

    Args:
        scoped_session_key: The session key without the agent:<id>: prefix.
        derive_legacy: Optional list of functions for channel-specific legacy derivation.
    """
    tokens = set(scoped_session_key.split(":"))
    if "group" in tokens:
        return SessionChatType.GROUP
    if "channel" in tokens:
        return SessionChatType.CHANNEL
    if "direct" in tokens or "dm" in tokens:
        return SessionChatType.DIRECT

    # Built-in legacy patterns
    import re
    if re.match(r"^group:[^:]+$", scoped_session_key):
        return SessionChatType.GROUP
    if re.match(r"^(?:whatsapp:)?[^:]+@g\.us$", scoped_session_key):
        return SessionChatType.GROUP
    if re.match(r"^discord:(?:[^:]+:)?guild-[^:]+:channel-[^:]+$", scoped_session_key):
        return SessionChatType.CHANNEL

    # Custom legacy derivers
    if derive_legacy:
        for fn in derive_legacy:
            derived = fn(scoped_session_key)
            if derived is not None:
                return derived

    return SessionChatType.UNKNOWN
