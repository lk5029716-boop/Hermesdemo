"""Internal hook event payload factory.

Ported from OpenClaw src/test-utils/internal-hook-event-payload.ts
"""

from __future__ import annotations

from datetime import datetime


def create_internal_hook_event_payload(
    type: str,
    action: str,
    session_key: str,
    context: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create a standardized internal hook event payload."""
    return {
        "type": type,
        "action": action,
        "sessionKey": session_key,
        "context": context or {},
        "timestamp": datetime.now().isoformat(),
        "messages": [],
    }
