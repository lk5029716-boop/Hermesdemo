"""Realtime voice output activity tracker.

Ported from OpenClaw src/talk/output-activity-tracker.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RealtimeVoiceOutputActivityDelta:
    audio_ms: int | None = None
    source_audio_bytes: int | None = None
    sink_audio_bytes: int | None = None


@dataclass
class RealtimeVoiceOutputActivitySnapshot:
    audio_ms: int = 0
    chunks: int = 0
    source_audio_bytes: int = 0
    sink_audio_bytes: int = 0
    playback_started: bool = False
    stream_ending: bool = False
    last_audio_at: int | None = None
    playback_started_at: int | None = None


class RealtimeVoiceOutputActivityTracker:
    """Tracks output audio activity for realtime voice sessions."""

    def __init__(self, now: Any = None) -> None:
        self._now = now or (lambda: int(__import__("time").time() * 1000))
        self._audio_ms = 0
        self._chunks = 0
        self._source_audio_bytes = 0
        self._sink_audio_bytes = 0
        self._playback_started = False
        self._stream_ending = False
        self._last_audio_at: int | None = None
        self._playback_started_at: int | None = None

    def mark_stream_opened(self) -> None:
        self._stream_ending = False
        self._playback_started = False
        self._playback_started_at = None
        self._last_audio_at = None

    def mark_stream_ending(self) -> None:
        self._stream_ending = True

    def mark_playback_started(self) -> None:
        if not self._playback_started:
            self._playback_started = True
            self._playback_started_at = self._now()

    def mark_audio(self, delta: RealtimeVoiceOutputActivityDelta) -> None:
        self._audio_ms += max(0, delta.audio_ms or 0)
        self._source_audio_bytes += max(0, delta.source_audio_bytes or 0)
        self._sink_audio_bytes += max(0, delta.sink_audio_bytes or 0)
        self._chunks += 1
        self._last_audio_at = self._now()

    def reset(self) -> None:
        self._audio_ms = 0
        self._chunks = 0
        self._source_audio_bytes = 0
        self._sink_audio_bytes = 0
        self._playback_started = False
        self._stream_ending = False
        self._last_audio_at = None
        self._playback_started_at = None

    def is_active(self, sink_active: bool = False) -> bool:
        return sink_active or self._chunks > 0

    def is_interruptible(self, sink_active: bool = False) -> bool:
        return sink_active or self._chunks > 0 or self._audio_ms > 0

    def elapsed_playback_ms(self) -> int:
        if self._playback_started_at is None:
            return 0
        return self._now() - self._playback_started_at

    def playback_watchdog_delay_ms(
        self, margin_ms: int, min_ms: int = 1_000
    ) -> int | None:
        if self._playback_started_at is None or self._audio_ms <= 0:
            return None
        return max(min_ms, self._audio_ms - (self._now() - self._playback_started_at) + margin_ms)

    def snapshot(self) -> RealtimeVoiceOutputActivitySnapshot:
        return RealtimeVoiceOutputActivitySnapshot(
            audio_ms=self._audio_ms,
            chunks=self._chunks,
            source_audio_bytes=self._source_audio_bytes,
            sink_audio_bytes=self._sink_audio_bytes,
            playback_started=self._playback_started,
            stream_ending=self._stream_ending,
            last_audio_at=self._last_audio_at,
            playback_started_at=self._playback_started_at,
        )


def create_realtime_voice_output_activity_tracker(
    now: Any = None,
) -> RealtimeVoiceOutputActivityTracker:
    return RealtimeVoiceOutputActivityTracker(now=now)
