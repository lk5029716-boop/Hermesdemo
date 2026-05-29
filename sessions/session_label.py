"""Session label parsing.

Ported from OpenClaw src/sessions/session-label.ts
"""

from __future__ import annotations

SESSION_LABEL_MAX_LENGTH = 512


def parse_session_label(raw: object) -> "ParsedSessionLabel":
    """Validate and parse a session label string."""
    if not isinstance(raw, str):
        return ParsedSessionLabel(ok=False, error="invalid label: must be a string")
    trimmed = raw.strip()
    if not trimmed:
        return ParsedSessionLabel(ok=False, error="invalid label: empty")
    if len(trimmed) > SESSION_LABEL_MAX_LENGTH:
        return ParsedSessionLabel(
            ok=False,
            error=f"invalid label: too long (max {SESSION_LABEL_MAX_LENGTH})",
        )
    return ParsedSessionLabel(ok=True, label=trimmed)


class ParsedSessionLabel:
    """Result of parsing a session label."""

    def __init__(self, ok: bool, label: str = "", error: str = "") -> None:
        self.ok = ok
        self.label = label
        self.error = error

    def __repr__(self) -> str:
        if self.ok:
            return f"ParsedSessionLabel(ok=True, label={self.label!r})"
        return f"ParsedSessionLabel(ok=False, error={self.error!r})"
