"""Task completion contract — detect progress-only vs final deliverable completions.

Ported from OpenClaw src/tasks/task-completion-contract.ts
"""

from __future__ import annotations

from dataclasses import dataclass
import re


_PROGRESS_ONLY_PATTERN = re.compile(
    r"^(?:i(?:'|')ll|i will|i(?:'|')m|i am|i(?:'|')m going to|i am going to|let me|i need to)\s+(?:now\s+)?(?:analyz(?:e|ing)|apply|check(?:ing)?|continue|debug(?:ging)?|follow(?:ing)?\s+up|inspect(?:ing)?|investigat(?:e|ing)|look(?:ing)?(?:\s+into)?|map(?:ping)?|open(?:ing)?|read(?:ing)?|report(?:ing)?(?:\s+back)?|review(?:ing)?|run(?:ning)?|start(?:ing)?|test(?:ing)?|trace|trac(?:e|ing)|try(?:ing)?|update|verify(?:ing)?|work(?:ing)?)",
    re.IGNORECASE,
)

_BARE_PROGRESS_ONLY_PATTERN = re.compile(
    r"^(?:analyz(?:e|ing)|check(?:ing)?|debug(?:ging)?|inspect(?:ing)?|investigat(?:e|ing)|look(?:ing)?\s+into|map(?:ping)?|read(?:ing)?|report(?:ing)?\s+back|review(?:ing)?|run(?:ning)?|test(?:ing)?|trac(?:e|ing)|verify(?:ing)?|work(?:ing)?\s+on)\b",
    re.IGNORECASE,
)

_FOLLOW_UP_PLANNING_PREFIX_PATTERN = re.compile(
    r"^(?:after(?:wards|\s+that)?|from\s+there|next|once\s+(?:done|that(?:'|')s\s+done|that\s+is\s+done)|then)[,.]+",
    re.IGNORECASE,
)


@dataclass
class RequiredCompletionTerminalResult:
    terminal_outcome: str | None = None  # "blocked" or None
    terminal_summary: str | None = None


def _normalize_completion_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _normalize_completion_failure_reason(value: str | None) -> str:
    normalized = _normalize_completion_text(value)
    if not normalized:
        return ""
    return normalized if len(normalized) <= 160 else f"{normalized[:159]}..."


def _matches_progress_only_prefix(value: str) -> bool:
    if bool(_PROGRESS_ONLY_PATTERN.match(value)) or bool(_BARE_PROGRESS_ONLY_PATTERN.match(value)):
        return True
    followup = _FOLLOW_UP_PLANNING_PREFIX_PATTERN.sub("", value).strip()
    return bool(
        followup != value
        and bool(_PROGRESS_ONLY_PATTERN.match(followup) or _BARE_PROGRESS_ONLY_PATTERN.match(followup))
    )


def _has_non_progress_followup_sentence(value: str) -> bool:
    boundary = re.search(r"(?:[.!?:]|\s[-\u2013\u2014])\s+\S", value)
    if not boundary:
        return False
    separator_end = boundary.start() + len(boundary.group()) - 1
    first_sentence = value[:separator_end].strip()
    rest = value[separator_end:].strip()
    return _matches_progress_only_prefix(first_sentence) and not _is_progress_only_completion_text(rest)


def _is_progress_only_completion_text(value: str | None) -> bool:
    normalized = _normalize_completion_text(value)
    if not normalized:
        return False
    if _has_non_progress_followup_sentence(normalized):
        return False
    return _matches_progress_only_prefix(normalized)


def is_progress_only_completion_text(value: str | None) -> bool:
    """Check if completion text is only describing in-progress work, not a final deliverable.

    Examples of progress-only text:
        "I'll now analyze the code..."
        "Let me check the logs..."
        "I'm going to run the tests..."

    These indicate the task is still in progress, not delivering a final result.
    """
    return _is_progress_only_completion_text(value)


def resolve_required_completion_terminal_result(
    result_text: str | None,
) -> RequiredCompletionTerminalResult:
    """Determine if a required completion produced a final deliverable or was blocked."""
    normalized = _normalize_completion_text(result_text)
    if not normalized:
        return RequiredCompletionTerminalResult(
            terminal_outcome="blocked",
            terminal_summary="Required completion did not produce a final deliverable.",
        )
    if _is_progress_only_completion_text(normalized):
        return RequiredCompletionTerminalResult(
            terminal_outcome="blocked",
            terminal_summary="Required completion ended with progress-only text, not a final deliverable.",
        )
    return RequiredCompletionTerminalResult()


def resolve_required_completion_delivery_failure_terminal_result(
    reason: str | None,
) -> RequiredCompletionTerminalResult:
    """Create a terminal result for delivery failures."""
    normalized_reason = _normalize_completion_failure_reason(reason)
    if normalized_reason:
        summary = f"Required completion delivery failed before reaching the requester: {normalized_reason}."
    else:
        summary = "Required completion delivery failed before reaching the requester."
    return RequiredCompletionTerminalResult(terminal_outcome="blocked", terminal_summary=summary)
