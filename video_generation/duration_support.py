"""
duration_support.py — Duration snapping for video generation.

Adapted from OpenClaw src/video-generation/duration-support.ts.

Resolves which durations a provider+model supports and snaps
a requested duration to the closest supported value. Hermes has
no duration negotiation — it just sends whatever the user requests.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Set

from video_types import VideoGenerationProviderCapabilities
from capabilities import resolve_mode_capabilities


def _unique_sorted(values: List[int]) -> Optional[List[int]]:
    """Deduplicate, filter valid, and sort."""
    filtered = sorted(set(v for v in values if v > 0))
    return filtered if filtered else None


def resolve_supported_durations(
    capabilities: Optional[VideoGenerationProviderCapabilities],
    model: Optional[str] = None,
    input_image_count: int = 0,
    input_video_count: int = 0,
) -> Optional[List[int]]:
    """
    Get the list of supported durations (seconds) for a provider+model+mode.
    Returns None if durations are not constrained.
    """
    mode, caps = resolve_mode_capabilities(
        capabilities, model, input_image_count, input_video_count
    )
    if caps is None:
        return None

    model_name = model.strip() if model else ""

    # Check model-specific durations first
    if model_name:
        supported_by_model = getattr(caps, 'supportedDurationSecondsByModel', None)
        if supported_by_model and model_name in supported_by_model:
            return _unique_sorted(supported_by_model[model_name])

    # Fall back to mode-level durations
    mode_durations = getattr(caps, 'supportedDurationSeconds', None)
    if mode_durations:
        return _unique_sorted(mode_durations)

    return None


def snap_duration(
    duration_seconds: Optional[int],
    supported: Optional[List[int]],
) -> Optional[int]:
    """
    Snap a requested duration to the closest supported value.
    If no supported list, return the duration as-is (rounded, minimum 1).
    On tie, prefer the larger duration.
    """
    if duration_seconds is None or not math.isfinite(duration_seconds):
        return None

    rounded = max(1, round(duration_seconds))

    if not supported:
        return rounded

    best = supported[0]
    best_dist = abs(best - rounded)

    for val in supported[1:]:
        dist = abs(val - rounded)
        if dist < best_dist:
            best = val
            best_dist = dist
        elif dist == best_dist and val > best:
            # Tie-break: prefer larger
            best = val

    return best


def normalize_duration(
    capabilities: Optional[VideoGenerationProviderCapabilities],
    model: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    input_image_count: int = 0,
    input_video_count: int = 0,
) -> tuple[Optional[int], Optional[List[int]]]:
    """
    Resolve: given a provider+model+mode+requested duration,
    return (snapped_duration, supported_durations_list).

    This is the single entry point that combines resolution + snapping.
    """
    supported = resolve_supported_durations(
        capabilities, model, input_image_count, input_video_count
    )
    result = snap_duration(duration_seconds, supported)
    return result, supported
