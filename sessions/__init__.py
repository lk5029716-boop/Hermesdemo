"""Session management utilities.

Ported from OpenClaw src/sessions/

Provides:
    - Session ID validation (UUID format)
    - Session label parsing
    - Session chat type derivation
    - Session lifecycle event emitter
    - Session transcript update event emitter
"""

from .session_chat_type import SessionChatType, derive_session_chat_type_from_scoped_key
from .session_id import looks_like_session_id
from .session_label import ParsedSessionLabel, parse_session_label
from .session_lifecycle_events import (
    SessionLifecycleEvent,
    emit_session_lifecycle_event,
    on_session_lifecycle_event,
)
from .transcript_events import (
    SessionTranscriptUpdate,
    emit_session_transcript_update,
    on_session_transcript_update,
)

__all__ = [
    "ParsedSessionLabel",
    "SessionChatType",
    "SessionLifecycleEvent",
    "SessionTranscriptUpdate",
    "derive_session_chat_type_from_scoped_key",
    "emit_session_lifecycle_event",
    "emit_session_transcript_update",
    "looks_like_session_id",
    "on_session_lifecycle_event",
    "on_session_transcript_update",
    "parse_session_label",
]
