"""Session lifecycle event emitter.

Ported from OpenClaw src/sessions/session-lifecycle-events.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class SessionLifecycleEvent:
    session_key: str
    reason: str
    parent_session_key: str | None = None
    label: str | None = None
    display_name: str | None = None


SessionLifecycleListener = Callable[[SessionLifecycleEvent], None]

_SESSION_LIFECYCLE_LISTENERS: set[SessionLifecycleListener] = set()


def on_session_lifecycle_event(listener: SessionLifecycleListener) -> Callable[[], None]:
    """Register a listener for session lifecycle events. Returns an unsubscribe function."""
    _SESSION_LIFECYCLE_LISTENERS.add(listener)
    return lambda: _SESSION_LIFECYCLE_LISTENERS.discard(listener)


def emit_session_lifecycle_event(event: SessionLifecycleEvent) -> None:
    """Emit a session lifecycle event to all registered listeners."""
    for listener in _SESSION_LIFECYCLE_LISTENERS:
        try:
            listener(event)
        except Exception:
            pass  # Best-effort, do not propagate listener errors
