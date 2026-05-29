"""
model_ref.py — Provider/model string parsing.

Adapted from OpenClaw src/video-generation/model-ref.ts.

Parses "provider/model" strings into structured references.
Hermes has inline parsing; this is a centralized utility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelRef:
    """Parsed provider/model reference."""
    provider: str
    model: str


def parse_model_ref(raw: Optional[str]) -> Optional[ModelRef]:
    """
    Parse a "provider/model" string.

    Examples:
        "fal-ai/kling-v2-5-turbo" → ModelRef("fal-ai", "kling-v2-5-turbo")
        "runway/gen-4-turbo"       → ModelRef("runway", "gen-4-turbo")
        "minimax"                  → ModelRef("minimax", "")
    """
    if not raw or not raw.strip():
        return None

    raw = raw.strip()

    # Handle provider/model format
    if "/" in raw:
        parts = raw.split("/", 1)
        provider = parts[0].strip()
        model = parts[1].strip() if len(parts) > 1 else ""
        if provider:
            return ModelRef(provider=provider, model=model)
        return None

    # Provider-only (model inferred)
    provider = raw.strip()
    return ModelRef(provider=provider, model="") if provider else None


def resolve_model_string(raw: str, default_model: str = "") -> str:
    """
    Extract just the model name from a "provider/model" string.
    If no provider prefix, return the string as-is.
    """
    ref = parse_model_ref(raw)
    if ref is None:
        return raw
    return ref.model or default_model
