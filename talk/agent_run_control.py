"""Realtime voice agent run control — intent classification.

Ported from OpenClaw src/talk/agent-run-control-shared.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RealtimeVoiceAgentControlMode(str, Enum):
    STATUS = "status"
    STEER = "steer"
    CANCEL = "cancel"
    FOLLOWUP = "followup"


REALTIME_VOICE_AGENT_CONTROL_MODES = [e.value for e in RealtimeVoiceAgentControlMode]
REALTIME_VOICE_AGENT_CONTROL_TOOL_NAME = "openclaw_agent_control"


@dataclass
class RealtimeVoiceAgentControlTool:
    type: str = "function"
    name: str = REALTIME_VOICE_AGENT_CONTROL_TOOL_NAME
    description: str = (
        "Control an active OpenClaw tool-backed voice run. Use this when the caller "
        "asks in any language for status/progress, cancellation, a redirect/change to "
        "the active work, or a follow-up after the current work."
    )
    parameters: dict[str, Any] = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The caller's exact spoken request."},
            "mode": {
                "type": "string",
                "enum": REALTIME_VOICE_AGENT_CONTROL_MODES,
                "description": "status for progress questions, cancel for stop/abort, "
                "steer for changing the current work, followup for work to do after.",
            },
        },
        "required": ["text", "mode"],
    })


@dataclass
class RealtimeVoiceAgentControlIntent:
    mode: RealtimeVoiceAgentControlMode
    confidence: str  # "high" | "medium" | "low"
    reason: str
    should_auto_control: bool


@dataclass
class RealtimeVoiceAgentRunActivity:
    active_work_kind: str | None = None
    has_active_embedded_run: bool | None = None
    active_tool_name: str | None = None
    active_tool_call_id: str | None = None
    active_tool_age_ms: int | None = None
    last_progress_age_ms: int | None = None
    last_progress_reason: str | None = None


@dataclass
class RealtimeVoiceAgentControlResult:
    ok: bool
    mode: str
    session_key: str
    active: bool
    session_id: str | None = None
    queued: bool | None = None
    aborted: bool | None = None
    target: str | None = None
    reason: str | None = None
    message: str = ""
    speak: bool = True
    show: bool = True
    suppress: bool = False
    provider_result: dict[str, str] | None = None
    enqueued_at_ms: int | None = None
    delivered_at_ms: int | None = None


# Pattern lists for intent classification
_CANCEL_PATTERNS = [
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?(?:cancel|cancle|abort)(?:\s+(?:that|this|it|the\s+(?:check|run|task|work)))?(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?(?:never mind|nevermind|forget it|kill it|end that)(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?stop(?:\s+(?:that|this|it|the\s+(?:check|run|task|work)))?(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:can|could|would)\s+you\s+(?:please\s+)?(?:cancel|cancle|stop|abort)(?:\s+(?:that|this|it|the\s+(?:check|run|task|work)))?(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right|actually)[,\s]+)?(?:can|could|would)\s+(?:we|you)\s+(?:just\s+)?(?:cancel|cancle|stop|abort)(?:\s+(?:that|this|it|the\s+(?:check|run|task|work)))?(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"\b(?:cancel|cancle|stop|abort)\s+(?:that|this|it|the\s+(?:check|run|task|work))\b", re.IGNORECASE),
]

_STATUS_PATTERNS = [
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:status|progress|update)(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:give me|what'?s|any)\s+(?:an?\s+)?update(?:\s*[.!?])?$", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(where are we|what'?s happening|what (?:are you|is it) doing|what'?s it doing|how (?:is|are) (?:it|you|that|this) going|how'?s it going|are you still working|is it done|did it finish)(\b|[.!?])", re.IGNORECASE),
]

_FOLLOWUP_PATTERNS = [
    re.compile(r"^(after that|when you'?re done|when it'?s done|next|then|also|one more thing|follow up)(\b|[,.!?])", re.IGNORECASE),
]

_STEER_PATTERNS = [
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?update\s+\S", re.IGNORECASE),
    re.compile(r"^(?:actually|instead|change|switch|focus|use|try|prefer|make|do|check|look at|go with|redirect|steer|tell it to)\b", re.IGNORECASE),
    re.compile(r"^(?:can|could|would)\s+you\s+(?:actually\s+)?(?:change|switch|focus|use|try|prefer|make|do|check|look at|go with|redirect|steer)\b", re.IGNORECASE),
    re.compile(r"\b(?:instead|not that|rather than|change that|switch to|focus on|use the|try the|go with|tell it to)\b", re.IGNORECASE),
]

_STOP_REDIRECT_PATTERNS = [
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?stop\s+(?:using|doing|checking|looking at|focusing on|trying)\b", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:can|could|would)\s+(?:you|we)\s+(?:please\s+)?stop\s+(?:using|doing|checking|looking at|focusing on|trying)\b", re.IGNORECASE),
    re.compile(r"^(?:(?:ok|okay|alright|all right)[,\s]+)?(?:please\s+)?stop\s+(?:that|this|it|the\s+(?:check|run|task|work))\s+from\b", re.IGNORECASE),
]


def _matches_any(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def _has_negated_cancel(text: str) -> bool:
    return bool(
        re.search(r"\b(?:don'?t|do\s+not|not|never)\s+(?:please\s+)?(?:cancel|cancle|stop|abort|kill|end)\b", text)
        or re.search(r"\bstop\s+(?:it|that|this)\s+from\b", text)
    )


def resolve_realtime_voice_agent_control_intent(
    text: str,
    mode: Any = None,
) -> RealtimeVoiceAgentControlIntent:
    """Classify user text into a control intent (cancel/steer/status/followup)."""
    if mode:
        mode_str = str(mode).strip().lower()
        if mode_str in REALTIME_VOICE_AGENT_CONTROL_MODES:
            return RealtimeVoiceAgentControlIntent(
                mode=RealtimeVoiceAgentControlMode(mode_str),
                confidence="high",
                reason="explicit_mode",
                should_auto_control=True,
            )

    normalized = text.strip().lower()

    if _matches_any(normalized, _STOP_REDIRECT_PATTERNS):
        return RealtimeVoiceAgentControlIntent(
            mode=RealtimeVoiceAgentControlMode.STEER,
            confidence="medium",
            reason="steer_command",
            should_auto_control=True,
        )

    if not _has_negated_cancel(normalized) and _matches_any(normalized, _CANCEL_PATTERNS):
        return RealtimeVoiceAgentControlIntent(
            mode=RealtimeVoiceAgentControlMode.CANCEL,
            confidence="high",
            reason="cancel_safety",
            should_auto_control=True,
        )

    if _matches_any(normalized, _STATUS_PATTERNS):
        return RealtimeVoiceAgentControlIntent(
            mode=RealtimeVoiceAgentControlMode.STATUS,
            confidence="high",
            reason="status_query",
            should_auto_control=True,
        )

    if _matches_any(normalized, _FOLLOWUP_PATTERNS):
        return RealtimeVoiceAgentControlIntent(
            mode=RealtimeVoiceAgentControlMode.FOLLOWUP,
            confidence="high",
            reason="followup_marker",
            should_auto_control=True,
        )

    if _matches_any(normalized, _STEER_PATTERNS):
        return RealtimeVoiceAgentControlIntent(
            mode=RealtimeVoiceAgentControlMode.STEER,
            confidence="medium",
            reason="steer_command",
            should_auto_control=True,
        )

    return RealtimeVoiceAgentControlIntent(
        mode=RealtimeVoiceAgentControlMode.STATUS,
        confidence="low",
        reason="safe_default",
        should_auto_control=False,
    )


def classify_realtime_voice_agent_control_text(text: str) -> str:
    """Classify user text into a control mode string."""
    return resolve_realtime_voice_agent_control_intent(text).mode.value


def should_auto_control_realtime_voice_agent_text(text: str) -> bool:
    """Check if the text should trigger automatic agent control."""
    return resolve_realtime_voice_agent_control_intent(text).should_auto_control


def build_realtime_voice_agent_cancel_provider_result(
    message: str = "Cancelled the active OpenClaw run.",
) -> dict[str, str]:
    return {"status": "cancelled", "message": message}


def build_realtime_voice_agent_followup_steering_text(text: str) -> str:
    return "\n".join([
        "Spoken follow-up for the current voice call.",
        "If you are mid-task, incorporate this after the current step or result unless it directly changes the current task.",
        "",
        text,
    ])


def format_realtime_voice_agent_queue_rejection(mode: str, reason: str) -> str:
    if reason == "compacting":
        return "OpenClaw is compacting the active run and cannot accept voice steering yet."
    if reason == "not_streaming":
        return "OpenClaw has an active run, but it is not currently accepting steering."
    if mode == "followup":
        return "OpenClaw could not queue that follow-up."
    return "OpenClaw could not steer the active run."
