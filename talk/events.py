"""Talk event types and sequencer.

Ported from OpenClaw src/talk/talk-events.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TalkEventType(str, Enum):
    SESSION_STARTED = "session.started"
    SESSION_READY = "session.ready"
    SESSION_CLOSED = "session.closed"
    SESSION_ERROR = "session.error"
    SESSION_REPLACED = "session.replaced"
    TURN_STARTED = "turn.started"
    TURN_ENDED = "turn.ended"
    TURN_CANCELLED = "turn.cancelled"
    CAPTURE_STARTED = "capture.started"
    CAPTURE_STOPPED = "capture.stopped"
    CAPTURE_CANCELLED = "capture.cancelled"
    CAPTURE_ONCE = "capture.once"
    INPUT_AUDIO_DELTA = "input.audio.delta"
    INPUT_AUDIO_COMMITTED = "input.audio.committed"
    TRANSCRIPT_DELTA = "transcript.delta"
    TRANSCRIPT_DONE = "transcript.done"
    OUTPUT_TEXT_DELTA = "output.text.delta"
    OUTPUT_TEXT_DONE = "output.text.done"
    OUTPUT_AUDIO_STARTED = "output.audio.started"
    OUTPUT_AUDIO_DELTA = "output.audio.delta"
    OUTPUT_AUDIO_DONE = "output.audio.done"
    TOOL_CALL = "tool.call"
    TOOL_PROGRESS = "tool.progress"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    USAGE_METRICS = "usage.metrics"
    LATENCY_METRICS = "latency.metrics"
    HEALTH_CHANGED = "health.changed"


ALL_TALK_EVENT_TYPES = [e.value for e in TalkEventType]


class TalkMode(str, Enum):
    REALTIME = "realtime"
    STT_TTS = "stt-tts"
    TRANSCRIPTION = "transcription"


class TalkTransport(str, Enum):
    WEBRTC = "webrtc"
    PROVIDER_WEBSOCKET = "provider-websocket"
    GATEWAY_RELAY = "gateway-relay"
    MANAGED_ROOM = "managed-room"


class TalkBrain(str, Enum):
    AGENT_CONSULT = "agent-consult"
    DIRECT_TOOLS = "direct-tools"
    NONE = "none"


@dataclass
class TalkEventContext:
    session_id: str
    mode: TalkMode
    transport: TalkTransport
    brain: TalkBrain
    provider: str | None = None


@dataclass
class TalkEvent:
    session_id: str
    mode: str
    transport: str
    brain: str
    id: str
    type: str
    seq: int
    timestamp: str
    payload: Any
    provider: str | None = None
    turn_id: str | None = None
    capture_id: str | None = None
    final: bool | None = None
    call_id: str | None = None
    item_id: str | None = None
    parent_id: str | None = None


@dataclass
class TalkEventInput:
    type: str
    payload: Any
    turn_id: str | None = None
    capture_id: str | None = None
    timestamp: str | None = None
    final: bool | None = None
    call_id: str | None = None
    item_id: str | None = None
    parent_id: str | None = None


# Turn-scoped event types
TURN_SCOPED_TYPES = {
    TalkEventType.TURN_STARTED,
    TalkEventType.TURN_ENDED,
    TalkEventType.TURN_CANCELLED,
    TalkEventType.INPUT_AUDIO_DELTA,
    TalkEventType.INPUT_AUDIO_COMMITTED,
    TalkEventType.TRANSCRIPT_DELTA,
    TalkEventType.TRANSCRIPT_DONE,
    TalkEventType.OUTPUT_TEXT_DELTA,
    TalkEventType.OUTPUT_TEXT_DONE,
    TalkEventType.OUTPUT_AUDIO_STARTED,
    TalkEventType.OUTPUT_AUDIO_DELTA,
    TalkEventType.OUTPUT_AUDIO_DONE,
    TalkEventType.TOOL_CALL,
    TalkEventType.TOOL_PROGRESS,
    TalkEventType.TOOL_RESULT,
    TalkEventType.TOOL_ERROR,
}

# Capture-scoped event types
CAPTURE_SCOPED_TYPES = {
    TalkEventType.CAPTURE_STARTED,
    TalkEventType.CAPTURE_STOPPED,
    TalkEventType.CAPTURE_CANCELLED,
    TalkEventType.CAPTURE_ONCE,
}


def _assert_talk_event_correlation(input: TalkEventInput) -> None:
    if input.type in [e.value for e in TURN_SCOPED_TYPES] and not input.turn_id:
        raise ValueError(f"Talk event {input.type} requires turnId")
    if input.type in [e.value for e in CAPTURE_SCOPED_TYPES] and not input.capture_id:
        raise ValueError(f"Talk event {input.type} requires captureId")


class TalkEventSequencer:
    """Sequentially numbers talk events within a session."""

    def __init__(
        self,
        context: TalkEventContext,
        now: Any = None,
    ) -> None:
        self._context = context
        self._seq = 0
        self._now = now or (lambda: __import__("datetime").datetime.now().isoformat())

    def next(self, input: TalkEventInput) -> TalkEvent:
        _assert_talk_event_correlation(input)
        self._seq += 1
        ts = input.timestamp or self._now()
        return TalkEvent(
            session_id=self._context.session_id,
            mode=self._context.mode.value,
            transport=self._context.transport.value,
            brain=self._context.brain.value,
            provider=self._context.provider,
            id=f"{self._context.session_id}:{self._seq}",
            type=input.type,
            seq=self._seq,
            timestamp=ts,
            payload=input.payload,
            turn_id=input.turn_id,
            capture_id=input.capture_id,
            final=input.final,
            call_id=input.call_id,
            item_id=input.item_id,
            parent_id=input.parent_id,
        )


def create_talk_event_sequencer(
    context: TalkEventContext,
    now: Any = None,
) -> TalkEventSequencer:
    return TalkEventSequencer(context, now=now)
