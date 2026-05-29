"""Session transcript update event emitter.

Ported from OpenClaw src/sessions/transcript-events.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SessionTranscriptUpdate:
    session_file: str
    session_key: str | None = None
    message: object | None = None
    message_id: str | None = None
    message_seq: int | None = None


SessionTranscriptListener = Callable[[SessionTranscriptUpdate], None]

_SESSION_TRANSCRIPT_LISTENERS: set[SessionTranscriptListener] = set()


def on_session_transcript_update(listener: SessionTranscriptListener) -> Callable[[], None]:
    """Register a listener for session transcript updates. Returns an unsubscribe function."""
    _SESSION_TRANSCRIPT_LISTENERS.add(listener)
    return lambda: _SESSION_TRANSCRIPT_LISTENERS.discard(listener)


def emit_session_transcript_update(
    update: "str | SessionTranscriptUpdate",
) -> None:
    """Emit a session transcript update to all registered listeners."""
    if isinstance(update, str):
        normalized = SessionTranscriptUpdate(session_file=update)
    else:
        normalized = update

    if not normalized.session_file or not normalized.session_file.strip():
        return

    result = SessionTranscriptUpdate(
        session_file=normalized.session_file.strip(),
        session_key=normalized.session_key.strip() if normalized.session_key else None,
        message=normalized.message,
        message_id=normalized.message_id.strip() if normalized.message_id else None,
        message_seq=normalized.message_seq if normalized.message_seq and normalized.message_seq > 0 else None,
    )

    for listener in _SESSION_TRANSCRIPT_LISTENERS:
        try:
            listener(result)
        except Exception:
            pass
