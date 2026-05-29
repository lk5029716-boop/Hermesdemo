"""Realtime voice turn context tracker.

Ported from OpenClaw src/talk/turn-context-tracker.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_TURN_CONTEXT_LIMIT = 32
DEFAULT_IGNORED_CONTEXT_TTL_MS = 10_000


@dataclass
class RealtimeVoiceTurnContextHandle:
    id: str
    context: Any
    has_audio: bool = False
    closed: bool = False
    started_at: int = 0
    last_audio_at: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class RealtimeVoiceTurnContextTracker:
    """Manages turn contexts for realtime voice sessions with pruning."""

    def __init__(
        self,
        limit: int = DEFAULT_TURN_CONTEXT_LIMIT,
        ignored_context_ttl_ms: int = DEFAULT_IGNORED_CONTEXT_TTL_MS,
        now: Any = None,
        defer_until_audio: bool = False,
    ) -> None:
        self._limit = max(0, int(limit))
        self._ignored_ttl = max(0, int(ignored_context_ttl_ms))
        self._now = now or (lambda: int(__import__("time").time() * 1000))
        self._defer = defer_until_audio
        self._turns: list[RealtimeVoiceTurnContextHandle] = []
        self._ignored: tuple[Any, int] | None = None  # (context, created_at)
        self._next_id = 0

    def open(self, context: Any, **extra: Any) -> RealtimeVoiceTurnContextHandle:
        self._next_id += 1
        started_at = self._now()
        handle = RealtimeVoiceTurnContextHandle(
            id=f"realtime-turn:{started_at}:{self._next_id}",
            context=context,
            started_at=started_at,
            extra=extra,
        )
        if not self._defer:
            self._turns.append(handle)
            self._prune()
        return handle

    def mark_audio(self, handle: RealtimeVoiceTurnContextHandle) -> None:
        handle.has_audio = True
        handle.last_audio_at = self._now()
        if handle not in self._turns:
            self._turns.append(handle)
            self._prune()

    def close(self, handle: RealtimeVoiceTurnContextHandle) -> None:
        handle.closed = True
        if handle in self._turns:
            self._prune()

    def consume_audio_context(self) -> Any | None:
        self._prune()
        self._expire_closed_before_later_audio()
        for i, turn in enumerate(self._turns):
            if turn.has_audio:
                return self._turns.pop(i).context
        return None

    def peek_audio_turn(self) -> RealtimeVoiceTurnContextHandle | None:
        self._prune()
        self._expire_closed_before_later_audio()
        for turn in self._turns:
            if turn.has_audio:
                return turn
        return None

    def has_audio_context(self) -> bool:
        self._prune()
        self._expire_closed_before_later_audio()
        return any(t.has_audio for t in self._turns)

    def remember_ignored_context(self, context: Any) -> None:
        if context is not None:
            self._ignored = (context, self._now())

    def consume_ignored_context(self) -> Any | None:
        if self._ignored is None:
            return None
        ctx, created_at = self._ignored
        self._ignored = None
        if self._now() - created_at > self._ignored_ttl:
            return None
        return ctx

    def size(self) -> int:
        self._prune()
        return len(self._turns)

    def clear(self) -> None:
        self._turns.clear()
        self._ignored = None

    def _prune(self) -> None:
        self._turns = [t for t in self._turns if not (t.closed and not t.has_audio)]
        while len(self._turns) > self._limit:
            completed = next((i for i, t in enumerate(self._turns) if t.closed), 0)
            self._turns.pop(max(completed, 0))

    def _expire_closed_before_later_audio(self) -> None:
        has_later_audio = False
        for i in range(len(self._turns) - 1, -1, -1):
            turn = self._turns[i]
            if not turn.has_audio:
                continue
            if turn.closed and has_later_audio:
                self._turns.pop(i)
                continue
            has_later_audio = True


def create_realtime_voice_turn_context_tracker(
    limit: int = DEFAULT_TURN_CONTEXT_LIMIT,
    ignored_context_ttl_ms: int = DEFAULT_IGNORED_CONTEXT_TTL_MS,
    now: Any = None,
    defer_until_audio: bool = False,
) -> RealtimeVoiceTurnContextTracker:
    return RealtimeVoiceTurnContextTracker(
        limit=limit,
        ignored_context_ttl_ms=ignored_context_ttl_ms,
        now=now,
        defer_until_audio=defer_until_audio,
    )
