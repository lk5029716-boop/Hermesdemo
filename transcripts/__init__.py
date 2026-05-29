"""
transcripts — Meeting transcript parsing and summarization.

Adapted from OpenClaw src/transcripts/ (2 files selected from 6).

Provides:
- manual_source.py — parse speaker-labeled transcript text
- summary.py — generate meeting overview, decisions, action items, risks

Skipped 4 files: config.ts, provider-registry.ts, provider-types.ts, store.ts
(all depend on OpenClaw internals: config types, plugin system).
"""

from .manual_source import (
    parse_speaker_line,
    import_manual_transcript,
    TranscriptUtterance,
)
from .summary import (
    summarize_transcripts,
    render_transcripts_markdown,
    TranscriptUtterance as SummaryUtterance,
    TranscriptSessionDescriptor,
    TranscriptsSummary,
)

__all__ = [
    "parse_speaker_line",
    "import_manual_transcript",
    "TranscriptUtterance",
    "summarize_transcripts",
    "render_transcripts_markdown",
    "TranscriptSessionDescriptor",
    "TranscriptsSummary",
]
