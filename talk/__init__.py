"""Talk system — realtime voice event types, audio codec, and control logic.

Ported from OpenClaw src/talk/
"""

from .activation_name import (
    match_realtime_voice_activation_name,
    normalize_realtime_voice_activation_name,
    normalize_supported_realtime_voice_activation_name,
    sort_realtime_voice_activation_names,
)
from .agent_run_control import (
    REALTIME_VOICE_AGENT_CONTROL_MODES,
    REALTIME_VOICE_AGENT_CONTROL_TOOL_NAME,
    RealtimeVoiceAgentControlIntent,
    RealtimeVoiceAgentControlMode,
    RealtimeVoiceAgentControlResult,
    RealtimeVoiceAgentControlTool,
    RealtimeVoiceAgentRunActivity,
    build_realtime_voice_agent_cancel_provider_result,
    build_realtime_voice_agent_followup_steering_text,
    classify_realtime_voice_agent_control_text,
    format_realtime_voice_agent_queue_rejection,
    resolve_realtime_voice_agent_control_intent,
    should_auto_control_realtime_voice_agent_text,
)
from .audio_codec import (
    convert_pcm_to_mulaw_8k,
    mulaw_to_pcm,
    pcm_to_mulaw,
    resample_pcm,
    resample_pcm_to_8k,
)
from .consult import (
    classify_skippable_realtime_voice_consult_transcript,
    first_finite_talk_event_number,
    match_realtime_voice_questions,
    normalize_realtime_voice_consult_question,
    read_realtime_voice_consult_question,
    read_speakable_realtime_voice_tool_result,
)
from .events import (
    TalkBrain,
    TalkEvent,
    TalkEventContext,
    TalkEventInput,
    TalkEventSequencer,
    TalkEventType,
    TalkMode,
    TalkTransport,
    create_talk_event_sequencer,
)
from .output_activity_tracker import (
    RealtimeVoiceOutputActivityDelta,
    RealtimeVoiceOutputActivitySnapshot,
    RealtimeVoiceOutputActivityTracker,
    create_realtime_voice_output_activity_tracker,
)
from .provider_types import (
    RealtimeVoiceAudioFormat,
    RealtimeVoiceAudioFormatSpec,
    RealtimeVoiceBridgeCallbacks,
    RealtimeVoiceBridgeEvent,
    RealtimeVoiceCloseReason,
    RealtimeVoiceProviderCapabilities,
    RealtimeVoiceRole,
    RealtimeVoiceTool,
    RealtimeVoiceToolCallEvent,
    RealtimeVoiceToolResultOptions,
)
from .turn_context_tracker import (
    DEFAULT_IGNORED_CONTEXT_TTL_MS,
    DEFAULT_TURN_CONTEXT_LIMIT,
    RealtimeVoiceTurnContextHandle,
    RealtimeVoiceTurnContextTracker,
    create_realtime_voice_turn_context_tracker,
)

__all__ = [
    # Events
    "TalkBrain",
    "TalkEvent",
    "TalkEventContext",
    "TalkEventInput",
    "TalkEventSequencer",
    "TalkEventType",
    "TalkMode",
    "TalkTransport",
    "create_talk_event_sequencer",
    # Provider types
    "RealtimeVoiceAudioFormat",
    "RealtimeVoiceAudioFormatSpec",
    "RealtimeVoiceBridgeCallbacks",
    "RealtimeVoiceBridgeEvent",
    "RealtimeVoiceCloseReason",
    "RealtimeVoiceProviderCapabilities",
    "RealtimeVoiceRole",
    "RealtimeVoiceTool",
    "RealtimeVoiceToolCallEvent",
    "RealtimeVoiceToolResultOptions",
    # Audio codec
    "convert_pcm_to_mulaw_8k",
    "mulaw_to_pcm",
    "pcm_to_mulaw",
    "resample_pcm",
    "resample_pcm_to_8k",
    # Consult
    "classify_skippable_realtime_voice_consult_transcript",
    "first_finite_talk_event_number",
    "match_realtime_voice_questions",
    "normalize_realtime_voice_consult_question",
    "read_realtime_voice_consult_question",
    "read_speakable_realtime_voice_tool_result",
    # Activation name
    "match_realtime_voice_activation_name",
    "normalize_realtime_voice_activation_name",
    "normalize_supported_realtime_voice_activation_name",
    "sort_realtime_voice_activation_names",
    # Output activity
    "RealtimeVoiceOutputActivityDelta",
    "RealtimeVoiceOutputActivitySnapshot",
    "RealtimeVoiceOutputActivityTracker",
    "create_realtime_voice_output_activity_tracker",
    # Turn context
    "DEFAULT_IGNORED_CONTEXT_TTL_MS",
    "DEFAULT_TURN_CONTEXT_LIMIT",
    "RealtimeVoiceTurnContextHandle",
    "RealtimeVoiceTurnContextTracker",
    "create_realtime_voice_turn_context_tracker",
    # Agent run control
    "REALTIME_VOICE_AGENT_CONTROL_MODES",
    "REALTIME_VOICE_AGENT_CONTROL_TOOL_NAME",
    "RealtimeVoiceAgentControlIntent",
    "RealtimeVoiceAgentControlMode",
    "RealtimeVoiceAgentControlResult",
    "RealtimeVoiceAgentControlTool",
    "RealtimeVoiceAgentRunActivity",
    "build_realtime_voice_agent_cancel_provider_result",
    "build_realtime_voice_agent_followup_steering_text",
    "classify_realtime_voice_agent_control_text",
    "format_realtime_voice_agent_queue_rejection",
    "resolve_realtime_voice_agent_control_intent",
    "should_auto_control_realtime_voice_agent_text",
]
