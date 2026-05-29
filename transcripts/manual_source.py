"""
manual_source.py — Manual transcript import parser.

Adapted from OpenClaw src/transcripts/manual-source.ts.

Parses speaker-labeled transcript text into structured utterances.

Input format:
    Speaker One: Hello everyone
    Speaker Two: Hi there
    We discussed the project

Output: List of utterances with speaker labels.

No OpenClaw dependencies — pure parsing utility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TranscriptUtterance:
    """A single utterance in a transcript."""
    id: str
    session_id: str
    started_at: str
    final: bool
    speaker_label: str
    text: str


def parse_speaker_line(line: str) -> tuple[Optional[str], str]:
    """
    Parse a single line of transcript text.

    Format: "Speaker: text" or just "text" (if no speaker label).

    Returns (speaker_label_or_None, text).
    """
    match = re.match(r"^([^:\n]{1,80}):\s+(.+)$", line.strip())
    if not match:
        return None, line.strip()
    return match[1].strip(), match[2].strip() or ""


def import_manual_transcript(
    text: str,
    session_id: str,
    default_speaker: str = "Speaker",
) -> list[TranscriptUtterance]:
    """
    Import a full transcript from plain text.

    Splits by lines, parses speaker labels, filters empty lines.

    Args:
        text: Full transcript text (newline-separated)
        session_id: Session identifier to attach to utterances
        default_speaker: Default speaker name when not labeled

    Returns:
        List of TranscriptUtterance objects
    """
    now = datetime.now(timezone.utc).isoformat()
    lines = text.splitlines()
    utterances: list[TranscriptUtterance] = []

    for index, line in enumerate(lines):
        speaker_label, text_content = parse_speaker_line(line)
        if not text_content:
            continue
        utterances.append(TranscriptUtterance(
            id=f"{session_id}-{index + 1}",
            session_id=session_id,
            started_at=now,
            final=True,
            speaker_label=speaker_label or default_speaker,
            text=text_content,
        ))

    return utterances
