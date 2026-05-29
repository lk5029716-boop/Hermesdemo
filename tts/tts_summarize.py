"""
tts_summarize.py — LLM-based text summarization before TTS.

Adapted from OpenClaw src/tts/tts-core.ts.

Before sending text to TTS, this module summarizes long text using
an LLM to keep it within a target character limit. This prevents
TTS from timing out on long messages and reduces cost.

Hermes has no equivalent — it sends full text to TTS directly.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default summarization prompt
DEFAULT_SUMMARIZE_PROMPT = """\
Summarize the following text for text-to-speech.
Keep the summary under {max_chars} characters.
Preserve the key information and tone.
Output ONLY the summary, no preamble or explanation.

Text to summarize:
{text}
"""


async def summarize_for_tts(
    text: str,
    max_chars: int = 500,
    llm_call_fn=None,
    prompt_template: str | None = None,
) -> str:
    """
    Summarize text for TTS if it exceeds max_chars.

    Args:
        text: Original text
        max_chars: Target max characters for TTS input
        llm_call_fn: Async function that takes a prompt string and returns a response string
        prompt_template: Optional custom prompt template (must have {max_chars} and {text} placeholders)

    Returns:
        Summarized text (or original if already short enough)
    """
    if not text or not text.strip():
        return ""

    if len(text) <= max_chars:
        return text

    if llm_call_fn is None:
        logger.warning("No LLM function provided for TTS summarization; truncating instead")
        return _truncate_for_tts(text, max_chars)

    template = prompt_template or DEFAULT_SUMMARIZE_PROMPT
    prompt = template.format(max_chars=max_chars, text=text)

    try:
        summary = await llm_call_fn(prompt)
        if summary and summary.strip():
            result = summary.strip()
            if len(result) < len(text):
                logger.info(f"TTS summary: {len(text)} → {len(result)} chars")
                return result
    except Exception as e:
        logger.warning(f"TTS summarization failed: {e}; truncating instead")

    return _truncate_for_tts(text, max_chars)


def _truncate_for_tts(text: str, max_chars: int) -> str:
    """Truncate text at a sentence boundary near max_chars."""
    if len(text) <= max_chars:
        return text

    # Try to break at sentence boundary
    truncated = text[:max_chars]
    for break_char in [". ", "! ", "? ", "\n", "; "]:
        last_break = truncated.rfind(break_char)
        if last_break > max_chars // 2:
            return truncated[:last_break + 1].strip()

    # Fall back to word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        return truncated[:last_space].strip() + "…"

    return truncated.strip() + "…"
