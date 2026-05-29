"""
normalization.py — Override resolution for video generation.

Adapted from OpenClaw src/video-generation/normalization.ts.

Resolves user-requested overrides (size, aspect ratio, resolution,
duration, audio, watermark) against what the provider actually supports.
Returns what was applied, what was dropped, and what was normalized.

Hermes currently sends provider options without checking if they'll
be silently dropped or auto-adjusted. This gives the caller full
visibility into what actually happened.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from video_types import (
    VideoGenerationProviderCapabilities,
    VideoGenerationNormalization,
    VideoIgnoredOverride,
    VideoNormalizationEntry,
    VideoResolution,
    VIDEO_RESOLUTION_ORDER,
    ResolvedVideoGenerationOverrides,
)
from capabilities import resolve_mode_capabilities
from duration_support import normalize_duration


def _closest_resolution(requested: str) -> Optional[str]:
    """Find the closest supported resolution."""
    try:
        requested_idx = VIDEO_RESOLUTION_ORDER.index(VideoResolution(requested))
    except (ValueError, KeyError):
        # Unknown resolution — find closest by pixel height
        requested_height = _height_from_resolution(requested)
        if requested_height is None:
            return None
        best = None
        best_dist = float('inf')
        for res in VIDEO_RESOLUTION_ORDER:
            h = _height_from_resolution(res.value)
            if h is not None:
                dist = abs(h - requested_height)
                if dist < best_dist:
                    best = res.value
                    best_dist = dist
        return best

    if not VIDEO_RESOLUTION_ORDER:
        return None
    return VIDEO_RESOLUTION_ORDER[requested_idx] if requested_idx < len(VIDEO_RESOLUTION_ORDER) else VIDEO_RESOLUTION_ORDER[-1].value


def _height_from_resolution(res: str) -> Optional[int]:
    """Extract height from resolution string like '720P'."""
    try:
        return int(res.replace("P", "").strip())
    except (ValueError, AttributeError):
        return None


def _closest_match(value: str, supported: List[str]) -> Optional[str]:
    """Find the closest match for a string value in a supported list."""
    if value in supported:
        return value
    # Try case-insensitive
    value_lower = value.lower().strip()
    for s in supported:
        if s.lower().strip() == value_lower:
            return s
    return None


def resolve_overrides(
    capabilities: Optional[VideoGenerationProviderCapabilities],
    model: str,
    size: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    audio: Optional[bool] = None,
    watermark: Optional[bool] = None,
    input_image_count: int = 0,
    input_video_count: int = 0,
    user_overrides: Optional[Dict[str, Any]] = None,
) -> ResolvedVideoGenerationOverrides:
    """
    Resolve all user-requested overrides against provider capabilities.

    Returns a ResolvedVideoGenerationOverrides with:
    - The actual values that will be sent
    - ignored_overrides: list of what was dropped
    - normalization: what was changed and why
    """
    mode, caps = resolve_mode_capabilities(
        capabilities, model, input_image_count, input_video_count
    )

    ignored: List[VideoIgnoredOverride] = []
    normalization = VideoGenerationNormalization()

    # Start with user values
    final_size = size
    final_ar = aspect_ratio
    final_res = resolution
    final_audio = audio
    final_watermark = watermark

    if caps:
        supported_sizes = getattr(caps, 'sizes', None)
        supported_ars = getattr(caps, 'aspectRatios', None)
        supported_res = getattr(caps, 'resolutions', None)

        # --- Size ---
        if size and (supported_sizes or hasattr(caps, 'supportsSize')):
            if getattr(caps, 'supportsSize', False) and supported_sizes:
                matched = _closest_match(size, supported_sizes)
                if matched and matched != size:
                    normalization.size = VideoNormalizationEntry(requested=size, applied=matched)
                final_size = matched
            elif not getattr(caps, 'supportsSize', True):
                # Provider doesn't support size — try to translate to aspect ratio
                if aspect_ratio and getattr(caps, 'supportsAspectRatio', False) and supported_ars:
                    matched_ar = _closest_match(aspect_ratio, supported_ars)
                    if matched_ar:
                        final_ar = matched_ar
                        normalization.aspectRatio = VideoNormalizationEntry(
                            requested=aspect_ratio, applied=matched_ar, derivedFrom="size"
                        )
                    else:
                        ignored.append(VideoIgnoredOverride(key="size", value=size))
                else:
                    ignored.append(VideoIgnoredOverride(key="size", value=size))
                final_size = None

        # --- Aspect Ratio ---
        if aspect_ratio and (supported_ars or hasattr(caps, 'supportsAspectRatio')):
            if getattr(caps, 'supportsAspectRatio', False) and supported_ars:
                matched = _closest_match(aspect_ratio, supported_ars)
                if matched and matched != aspect_ratio:
                    normalization.aspectRatio = VideoNormalizationEntry(
                        requested=aspect_ratio, applied=matched
                    )
                elif matched is None:
                    # Sentinel value like "adaptive" — provider-specific, not parseable
                    ignored.append(VideoIgnoredOverride(key="aspectRatio", value=aspect_ratio))
                final_ar = matched
            elif not getattr(caps, 'supportsAspectRatio', True):
                # Translate to size if possible
                if final_size is None and final_ar and supported_sizes:
                    # Derive size from aspect ratio
                    matched_size = None  # Would need aspect ratio → size mapping
                    if matched_size:
                        final_size = matched_size
                        normalization.size = VideoNormalizationEntry(
                            requested=final_ar, applied=matched_size, derivedFrom="aspectRatio"
                        )
                    else:
                        ignored.append(VideoIgnoredOverride(key="aspectRatio", value=aspect_ratio))
                else:
                    ignored.append(VideoIgnoredOverride(key="aspectRatio", value=aspect_ratio))
                final_ar = None

        # --- Resolution ---
        if resolution and (supported_res or hasattr(caps, 'supportsResolution')):
            if getattr(caps, 'supportsResolution', False) and supported_res:
                matched = _closest_match(resolution, supported_res)
                if matched and matched != resolution:
                    normalization.resolution = VideoNormalizationEntry(
                        requested=resolution, applied=matched
                    )
                elif matched is None:
                    matched_closest = _closest_resolution(resolution)
                    if matched_closest:
                        final_res = matched_closest
                        normalization.resolution = VideoNormalizationEntry(
                            requested=resolution, applied=matched_closest
                        )
                    else:
                        ignored.append(VideoIgnoredOverride(key="resolution", value=resolution))
                else:
                    final_res = matched
            elif not getattr(caps, 'supportsResolution', True):
                ignored.append(VideoIgnoredOverride(key="resolution", value=resolution))
                final_res = None
        elif resolution and not getattr(caps, 'supportsResolution', True):
            ignored.append(VideoIgnoredOverride(key="resolution", value=resolution))
            final_res = None

        # --- Audio ---
        if audio is not None and not getattr(caps, 'supportsAudio', True):
            ignored.append(VideoIgnoredOverride(key="audio", value=audio))
            final_audio = None

        # --- Watermark ---
        if watermark is not None and not getattr(caps, 'supportsWatermark', True):
            ignored.append(VideoIgnoredOverride(key="watermark", value=watermark))
            final_watermark = None

    # Final pass: drop anything that has no caps and no support flag
    if caps and final_size and not getattr(caps, 'supportsSize', True):
        ignored.append(VideoIgnoredOverride(key="size", value=final_size))
        final_size = None
    if caps and final_ar and not getattr(caps, 'supportsAspectRatio', True):
        ignored.append(VideoIgnoredOverride(key="aspectRatio", value=final_ar))
        final_ar = None
    if caps and final_res and not getattr(caps, 'supportsResolution', True):
        ignored.append(VideoIgnoredOverride(key="resolution", value=final_res))
        final_res = None

    # --- Duration ---
    snapped_duration, supported_durations = normalize_duration(
        capabilities, model, duration_seconds, input_image_count, input_video_count
    )

    if (duration_seconds is not None and snapped_duration is not None
            and duration_seconds != snapped_duration):
        normalization.durationSeconds = VideoNormalizationEntry(
            requested=duration_seconds,
            applied=snapped_duration,
        )
        if supported_durations:
            normalization.durationSeconds.supportedValues = supported_durations

    # Set normalization only if something was normalized
    norm = normalization if any([
        normalization.size,
        normalization.aspectRatio,
        normalization.resolution,
        normalization.durationSeconds,
    ]) else None

    return ResolvedVideoGenerationOverrides(
        size=final_size,
        aspectRatio=final_ar,
        resolution=final_res,
        seconds=snapped_duration,
        supportedDurationSeconds=supported_durations,
        audio=final_audio,
        watermark=final_watermark,
        ignoredOverrides=ignored,
        normalization=norm,
    )


def has_normalization(norm: Optional[VideoGenerationNormalization]) -> bool:
    """Check if any normalization was applied."""
    if norm is None:
        return False
    return any([norm.size, norm.aspectRatio, norm.resolution, norm.durationSeconds])
