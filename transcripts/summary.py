"""
summary.py — Meeting transcript summarization.

Adapted from OpenClaw src/transcripts/summary.ts.

Generates meeting summaries with:
- Overview (first N sentences)
- Decisions (lines matching decision patterns)
- Action items (lines matching action patterns)
- Risks (lines matching risk patterns)
- Full formatted transcript

Uses regex pattern matching — no LLM required. Fast and deterministic.

Hermes has no equivalent meeting notes / transcript summarization system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# Patterns for extracting structured information from transcripts
ACTION_PATTERNS = re.compile(
    r"\b(todo|action|follow up|follow-up|assign|owner|next step|ship|fix|send|schedule)\b",
    re.IGNORECASE,
)
DECISION_PATTERNS = re.compile(
    r"\b(decided|decision|we will|we'll|agreed|approved|go with|ship it)\b",
    re.IGNORECASE,
)
RISK_PATTERNS = re.compile(
    r"\b(risk|blocked|blocker|concern|issue|problem|unknown|deadline|privacy|security)\b",
    re.IGNORECASE,
)


@dataclass
class TranscriptUtterance:
    """A single utterance in a transcript."""
    id: str = ""
    session_id: str = ""
    started_at: str = ""
    final: bool = True
    speaker_label: str = ""
    text: str = ""


@dataclass
class TranscriptSessionDescriptor:
    """Metadata about a transcript session."""
    session_id: str = ""
    title: str = ""
    channel: str = ""
    started_at: str = ""
    ended_at: str = ""
    participants: list[str] = field(default_factory=list)


@dataclass
class TranscriptsSummary:
    """Structured summary of a transcript session."""
    session_id: str = ""
    title: str = "Transcripts"
    generated_at: str = ""
    overview: str = ""
    transcript: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    utterance_count: int = 0


def _normalize_string_entries(entries: list[str]) -> list[str]:
    """Deduplicate and strip whitespace from string list."""
    seen: set[str] = set()
    result: list[str] = []
    for entry in entries:
        stripped = entry.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            result.append(stripped)
    return result


def _first_sentences(utterances: list[TranscriptUtterance], limit: int = 4) -> str:
    """Extract first N sentences from utterances as overview."""
    text = " ".join(u.text for u in utterances if u.text)
    sentences = re.split(r"[.!?]+", text)
    normalized = _normalize_string_entries([s.strip() for s in sentences if s.strip()])
    selected = normalized[:limit]
    return ". ".join(selected) + ("." if selected else "")


def _format_speaker_line(utterance: TranscriptUtterance) -> str:
    """Format an utterance as 'Speaker: text' or just 'text'."""
    text = utterance.text.strip()
    if not text:
        return ""
    speaker = utterance.speaker_label.strip()
    return f"{speaker}: {text}" if speaker else text


def _collect_matches(
    utterances: list[TranscriptUtterance],
    pattern: re.Pattern,
    max_items: int = 12,
) -> list[str]:
    """Find utterances matching a pattern and format them."""
    results: list[str] = []
    for u in utterances:
        if pattern.search(u.text):
            formatted = _format_speaker_line(u)
            if formatted:
                results.append(formatted)
    return results[:max_items]


def summarize_transcripts(
    session: TranscriptSessionDescriptor,
    utterances: list[TranscriptUtterance],
) -> TranscriptsSummary:
    """
    Generate a meeting summary from transcript utterances.

    Extracts overview, decisions, action items, and risks using
    regex pattern matching. No LLM required — fast and deterministic.

    Args:
        session: Session metadata (ID, title, etc.)
        utterances: List of transcript utterances

    Returns:
        TranscriptsSummary with extracted information
    """
    title = session.title.strip() or "Transcripts"
    overview = _first_sentences(utterances, limit=4) or "No transcript captured yet."

    return TranscriptsSummary(
        session_id=session.session_id,
        title=title,
        generated_at=datetime.now(timezone.utc).isoformat(),
        overview=overview,
        transcript=[_format_speaker_line(u) for u in utterances if u.text.strip()],
        decisions=_collect_matches(utterances, DECISION_PATTERNS),
        action_items=_collect_matches(utterances, ACTION_PATTERNS),
        risks=_collect_matches(utterances, RISK_PATTERNS),
        utterance_count=len(utterances),
    )


def render_transcripts_markdown(summary: TranscriptsSummary) -> str:
    """
    Render a TranscriptsSummary as Markdown.

    Returns a complete Markdown document with overview, transcript,
    decisions, action items, and risks sections.
    """
    def render_list(items: list[str]) -> str:
        if items:
            return "\n".join(f"- {item}" for item in items)
        return "- None captured"

    return "\n".join([
        f"# {summary.title}",
        "",
        f"Generated: {summary.generated_at}",
        f"Session: {summary.session_id}",
        "",
        "## Overview",
        summary.overview,
        "",
        "## Transcript",
        render_list(summary.transcript),
        "",
        "## Decisions",
        render_list(summary.decisions),
        "",
        "## Action Items",
        render_list(summary.action_items),
        "",
        "## Risks",
        render_list(summary.risks),
        "",
        f"Transcript utterances: {summary.utterance_count}",
    ])
