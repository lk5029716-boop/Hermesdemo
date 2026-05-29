"""
tts_directives.py — TTS directive parsing from messages.

Adapted from OpenClaw src/tts/directives.ts.

Parses TTS directives from message text:
- [[tts]] — generate TTS for this message
- [[tts:voice_name]] — TTS with specific voice
- [[tts:hide]] — hide text, only play audio
- [[tts:summary]] — summarize before TTS
- [[tts:lang:en-US]] — TTS in specific language
- [[no-tts]] — suppress TTS for this message

Hermes has no TTS directive system — voice_mode.py handles
activation but not per-message TTS control.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Matches [[tts]] or [[tts:...]] or [[no-tts]]
TTS_DIRECTIVE_PATTERN = re.compile(
    r"\[\[(tts(?::([^\[\]]+))?|no-tts)\]\]",
    re.IGNORECASE,
)


@dataclass
class TtsDirective:
    """A parsed TTS directive."""
    raw: str
    enabled: bool = True
    voice: str | None = None
    hide_text: bool = False
    summarize: bool = False
    language: str | None = None
    provider: str | None = None
    position: int = 0


@dataclass
class TtsDirectiveResult:
    """Result of parsing TTS directives from text."""
    text: str  # Text with directives removed
    directives: list[TtsDirective]
    has_tts: bool
    has_no_tts: bool

    @property
    def should_tts(self) -> bool:
        """Should TTS be generated? True if [[tts]] and no [[no-tts]]."""
        return self.has_tts and not self.has_no_tts

    @property
    def primary_directive(self) -> TtsDirective | None:
        """Get the first [[tts]] directive, if any."""
        for d in self.directives:
            if d.enabled:
                return d
        return None


def parse_tts_directives(text: str | None) -> TtsDirectiveResult:
    """
    Parse TTS directives from message text.

    Example:
        >>> result = parse_tts_directives("Hello [[tts:voice1]] world")
        >>> result.should_tts
        True
        >>> result.primary_directive.voice
        'voice1'
        >>> result.text
        'Hello  world'
    """
    if not text:
        return TtsDirectiveResult(text="", directives=[], has_tts=False, has_no_tts=False)

    directives: list[TtsDirective] = []
    has_tts = False
    has_no_tts = False

    for match in TTS_DIRECTIVE_PATTERN.finditer(text):
        raw = match.group(0)
        full_value = match.group(1) or ""
        detail = match.group(2)

        if full_value.lower() == "no-tts":
            has_no_tts = True
            directives.append(TtsDirective(raw=raw, enabled=False, position=match.start()))
            continue

        has_tts = True
        directive = TtsDirective(raw=raw, enabled=True, position=match.start())

        if detail:
            _parse_directive_detail(detail.strip(), directive)

        directives.append(directive)

    # Remove directives from text
    cleaned = TTS_DIRECTIVE_PATTERN.sub("", text)
    cleaned = re.sub(r"  +", " ", cleaned).strip()

    return TtsDirectiveResult(
        text=cleaned,
        directives=directives,
        has_tts=has_tts,
        has_no_tts=has_no_tts,
    )


def _parse_directive_detail(detail: str, directive: TtsDirective) -> None:
    """Parse the detail portion of a [[tts:...]] directive."""
    lowered = detail.lower()

    # Check for special keywords
    if lowered == "hide":
        directive.hide_text = True
        return
    if lowered == "summary":
        directive.summarize = True
        return

    # Check for lang: prefix
    if lowered.startswith("lang:"):
        directive.language = detail[5:].strip()
        return

    # Check for provider: prefix
    if lowered.startswith("provider:"):
        directive.provider = detail[9:].strip()
        return

    # Otherwise treat as voice name
    directive.voice = detail


def has_tts_directive(text: str | None) -> bool:
    """Check if text contains a [[tts]] directive."""
    if not text:
        return False
    return bool(re.search(r"\[\[tts(?::[^\[\]]+)?\]\]", text, re.IGNORECASE))


def has_no_tts_directive(text: str | None) -> bool:
    """Check if text contains a [[no-tts]] directive."""
    if not text:
        return False
    return "[[no-tts]]" in text.lower()


def strip_tts_directives(text: str | None) -> str:
    """Remove all TTS directives from text."""
    if not text:
        return ""
    return TTS_DIRECTIVE_PATTERN.sub("", text).strip()
