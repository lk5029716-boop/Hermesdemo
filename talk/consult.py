"""Event metrics and consult transcript/question helpers.

Ported from OpenClaw src/talk/event-metrics.ts, consult-transcript.ts, consult-question.ts
"""

from __future__ import annotations

import re
from typing import Any


def first_finite_talk_event_number(
    record: dict[str, Any] | None,
    keys: list[str],
) -> int | None:
    """Extract the first finite number value from a record matching given keys."""
    if not record:
        return None
    for key in keys:
        value = record.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    return None


# --- Transcript classification ---

REALTIME_VOICE_CONSULT_TRAILING_FRAGMENT_WORDS = {
    "a", "about", "an", "and", "as", "at", "because", "but", "by",
    "for", "from", "in", "of", "on", "or", "so", "that", "the",
    "then", "to", "with",
}


def classify_skippable_realtime_voice_consult_transcript(
    text: str,
) -> str | None:
    """Classify a transcript as skippable (empty, incomplete, trailing fragment, or non-actionable closing)."""
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    if not normalized:
        return "empty"
    if re.search(r"(\.\.\.|…)\s*$", normalized):
        return "incomplete-transcript"
    match = re.search(r"[a-z']+$", normalized)
    last_word = match.group().strip("'") if match else None
    if last_word and last_word in REALTIME_VOICE_CONSULT_TRAILING_FRAGMENT_WORDS:
        return "trailing-fragment"
    if (
        "?" not in normalized
        and (
            re.match(r"^(i'?ll|i will) be (right )?back\b", normalized)
            or re.search(r"\b(see you|bye(?:-bye)?|goodbye)\b", normalized)
        )
    ):
        return "non-actionable-closing"
    return None


# --- Consult question extraction ---

REALTIME_VOICE_CONSULT_QUESTION_STOPWORDS = {
    "a", "an", "and", "are", "can", "check", "could", "for", "in",
    "is", "it", "look", "me", "of", "on", "or", "please", "see",
    "that", "the", "this", "to", "would", "you",
}

DEFAULT_CONSULT_QUESTION_KEYS = ["question", "prompt", "query", "task"]
DEFAULT_SPEAKABLE_RESULT_KEYS = ["text", "result", "output", "error"]
DEFAULT_SPEAKABLE_RESULT_MAX_CHARS = 1_800


def read_realtime_voice_consult_question(
    args: Any,
    keys: list[str] | None = None,
) -> str | None:
    """Extract a consult question string from args (dict or string)."""
    keys = keys or DEFAULT_CONSULT_QUESTION_KEYS
    if isinstance(args, str):
        return args.strip() or None
    if not isinstance(args, dict):
        return None
    for key in keys:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_realtime_voice_consult_question(value: str | None) -> str | None:
    """Normalize a question string for comparison."""
    if not value:
        return None
    normalized = re.sub(r"[^\w]+", " ", value.lower()).strip()
    return normalized or None


def _consult_question_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^\w]+", value)
        if len(token) >= 2 and token not in REALTIME_VOICE_CONSULT_QUESTION_STOPWORDS
    }


def match_realtime_voice_questions(
    left: str | None,
    right: str | None,
    min_token_overlap_ratio: float = 0.6,
    min_token_overlap_count: int = 2,
) -> bool:
    """Check if two question strings match (containment or token overlap)."""
    norm_left = normalize_realtime_voice_consult_question(left)
    norm_right = normalize_realtime_voice_consult_question(right)
    if not norm_left or not norm_right:
        return False
    if norm_left == norm_right or norm_left in norm_right or norm_right in norm_left:
        return True
    left_tokens = _consult_question_tokens(norm_left)
    right_tokens = _consult_question_tokens(norm_right)
    if not left_tokens or not right_tokens:
        return False
    overlap = sum(1 for t in left_tokens if t in right_tokens)
    if overlap < min_token_overlap_count:
        return False
    return overlap / min(len(left_tokens), len(right_tokens)) >= min_token_overlap_ratio


def read_speakable_realtime_voice_tool_result(
    result: Any,
    keys: list[str] | None = None,
    max_chars: int = DEFAULT_SPEAKABLE_RESULT_MAX_CHARS,
    string_result: bool = True,
) -> str | None:
    """Extract a speakable string from a tool result."""
    keys = keys or DEFAULT_SPEAKABLE_RESULT_KEYS
    if isinstance(result, str):
        trimmed = result.strip()
        if not trimmed:
            return None
        if len(trimmed) > max_chars:
            return f"{trimmed[:max_chars - 16].strip()} [truncated]"
        return trimmed if string_result else None
    if not isinstance(result, dict):
        return None
    for key in keys:
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            trimmed = value.strip()
            if len(trimmed) > max_chars:
                return f"{trimmed[:max_chars - 16].strip()} [truncated]"
            return trimmed
    return None
