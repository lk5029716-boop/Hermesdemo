"""Realtime voice provider type definitions.

Ported from OpenClaw src/talk/provider-types.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class RealtimeVoiceRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class RealtimeVoiceCloseReason(str, Enum):
    COMPLETED = "completed"
    ERROR = "error"


class RealtimeVoiceAudioFormat(Enum):
    G711_ULAW_8KHZ = "g711_ulaw_8khz"
    PCM16_24KHZ = "pcm16_24khz"


@dataclass
class RealtimeVoiceAudioFormatSpec:
    encoding: str
    sample_rate_hz: int
    channels: int = 1


REALTIME_VOICE_AUDIO_FORMAT_G711_ULAW_8KHZ = RealtimeVoiceAudioFormatSpec(
    encoding="g711_ulaw", sample_rate_hz=8000, channels=1
)
REALTIME_VOICE_AUDIO_FORMAT_PCM16_24KHZ = RealtimeVoiceAudioFormatSpec(
    encoding="pcm16", sample_rate_hz=24000, channels=1
)


@dataclass
class RealtimeVoiceTool:
    type: str = "function"
    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RealtimeVoiceToolCallEvent:
    item_id: str
    call_id: str
    name: str
    args: Any


@dataclass
class RealtimeVoiceToolResultOptions:
    suppress_response: bool = False
    will_continue: bool = False


@dataclass
class RealtimeVoiceBridgeEvent:
    direction: str  # "client" | "server"
    type: str
    detail: str | None = None


@dataclass
class RealtimeVoiceProviderCapabilities:
    transports: list[str] = field(default_factory=list)
    input_audio_formats: list[RealtimeVoiceAudioFormatSpec] = field(default_factory=list)
    output_audio_formats: list[RealtimeVoiceAudioFormatSpec] = field(default_factory=list)
    supports_browser_session: bool = False
    supports_barge_in: bool = False
    supports_tool_calls: bool = False
    supports_video_frames: bool = False
    supports_session_resumption: bool = False


@dataclass
class RealtimeVoiceBridgeCallbacks:
    on_audio: Any  # Callable[[bytes], None] — using Any to avoid complex ctypes
    on_clear_audio: Any = None
    on_mark: Any = None
    on_transcript: Any = None
    on_event: Any = None
    on_tool_call: Any = None
    on_ready: Any = None
    on_error: Any = None
    on_close: Any = None
