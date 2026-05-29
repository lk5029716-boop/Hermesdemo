"""
tts — Text-to-speech utilities.

Adapted from OpenClaw src/tts/ (5 files selected from 14).

Adds per-message TTS control via [[ttts]] directive tags,
auto-mode normalization, text summarization before TTS,
and a generic OpenAI-compatible TTS adapter.
"""

from .tts_summarize import summarize_for_tts, _truncate_for_tts
from .tts_auto_mode import TtsAutoMode, normalize_auto_mode, should_tts
from .tts_validation import (
    is_empty_whitespace, trim_to_lines, bounded_int, bounded_float,
    bounded_value_from_ranges, normalize_language, validate_seed,
    cleanup_text_for_tts,
)
from .tts_directives import (
    parse_tts_directives, has_tts_directive, has_no_tts_directive,
    strip_tts_directives, TtsDirective, TtsDirectiveResult,
)
from .openai_tts_provider import (
    OpenAiCompatibleTtsProvider, TtsProviderOptions, TtsAudioResult, TtsError,
)

__all__ = [
    "summarize_for_tts",
    "TtsAutoMode", "normalize_auto_mode", "should_tts",
    "is_empty_whitespace", "trim_to_lines", "bounded_int", "bounded_float",
    "bounded_value_from_ranges", "normalize_language", "validate_seed",
    "cleanup_text_for_tts",
    "parse_tts_directives", "has_tts_directive", "has_no_tts_directive",
    "strip_tts_directives", "TtsDirective", "TtsDirectiveResult",
    "OpenAiCompatibleTtsProvider", "TtsProviderOptions", "TtsAudioResult", "TtsError",
]
