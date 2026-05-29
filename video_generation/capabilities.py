"""
capabilities.py — Video generation mode + capability resolution.

Adapted from OpenClaw src/video-generation/capabilities.ts.

Resolves the generation mode from input asset counts,
checks what modes a provider supports, and resolves per-model
capabilities. Hermes's video_gen_registry doesn't do this — it
just round-robins without capability checking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from video_types import (
    VideoGenerationMode,
    VideoGenerationModeCapabilities,
    VideoGenerationProviderCapabilities,
    VideoGenerationTransformCapabilities,
    VideoGenerationTransformCapabilities as TransformCaps,
)


def resolve_mode(
    input_image_count: int = 0,
    input_video_count: int = 0,
) -> Optional[VideoGenerationMode]:
    """
    Determine the generation mode from input asset count.

    Rules:
    - Mixed image+video input → not supported (returns None)
    - Video only → VIDEO_TO_VIDEO
    - Image only → IMAGE_TO_VIDEO
    - Neither → GENERATE (text-to-video)
    """
    if input_image_count > 0 and input_video_count > 0:
        return None
    if input_video_count > 0:
        return VideoGenerationMode.VIDEO_TO_VIDEO
    if input_image_count > 0:
        return VideoGenerationMode.IMAGE_TO_VIDEO
    return VideoGenerationMode.GENERATE


def list_supported_modes(
    capabilities: Optional[VideoGenerationProviderCapabilities],
) -> List[VideoGenerationMode]:
    """List which generation modes a provider supports."""
    modes = [VideoGenerationMode.GENERATE]
    if capabilities:
        i2v = capabilities.imageToVideo
        if i2v and i2v.enabled:
            modes.append(VideoGenerationMode.IMAGE_TO_VIDEO)
        v2v = capabilities.videoToVideo
        if v2v and v2v.enabled:
            modes.append(VideoGenerationMode.VIDEO_TO_VIDEO)
    return modes


def resolve_mode_capabilities(
    provider_caps: Optional[VideoGenerationProviderCapabilities] = None,
    model: Optional[str] = None,
    input_image_count: int = 0,
    input_video_count: int = 0,
) -> Tuple[Optional[VideoGenerationMode], Any]:
    """
    Resolve both the generation mode and its capabilities.

    Returns (mode, capabilities) where capabilities is the per-mode
    capability object (with model-specific overlays applied).

    If the mode is not supported, returns (None, None).
    """
    mode = resolve_mode(input_image_count, input_video_count)
    if mode is None:
        return None, None

    if provider_caps is None:
        return mode, None

    model_name = model.strip() if model else ""

    def apply_model_overlays(caps: Any) -> Any:
        """Apply per-model capability overrides if available."""
        if not caps or not model_name:
            return caps
        max_images_by_model = getattr(caps, 'maxInputImagesByModel', None)
        max_videos_by_model = getattr(caps, 'maxInputVideosByModel', None)
        max_audios_by_model = getattr(caps, 'maxInputAudiosByModel', None)

        max_images = max_images_by_model.get(model_name) if max_images_by_model else None
        max_videos = max_videos_by_model.get(model_name) if max_videos_by_model else None
        max_audios = max_audios_by_model.get(model_name) if max_audios_by_model else None

        if max_images is None and max_videos is None and max_audios is None:
            return caps

        # Build a copy with model-specific overrides
        caps_dict = {k: v for k, v in caps.__dict__.items() if v is not None}
        if max_images is not None:
            caps_dict['maxInputImages'] = max_images
        if max_videos is not None:
            caps_dict['maxInputVideos'] = max_videos
        if max_audios is not None:
            caps_dict['maxInputAudios'] = max_audios

        if isinstance(caps, TransformCaps):
            return TransformCaps(**caps_dict)
        return VideoGenerationModeCapabilities(**caps_dict)

    if mode == VideoGenerationMode.GENERATE:
        caps = getattr(provider_caps, 'generate', None)
        return mode, apply_model_overlays(caps)

    if mode == VideoGenerationMode.IMAGE_TO_VIDEO:
        caps = getattr(provider_caps, 'imageToVideo', None)
        return mode, apply_model_overlays(caps)

    if mode == VideoGenerationMode.VIDEO_TO_VIDEO:
        caps = getattr(provider_caps, 'videoToVideo', None)

        # Special case: mixed image+video input may be handled by videoToVideo
        if (input_image_count > 0 and input_video_count > 0
                and caps and caps.enabled and caps.maxInputImages > 0):
            return mode, apply_model_overlays(caps)

        caps = apply_model_overlays(caps)
        if not caps or not getattr(caps, 'enabled', False):
            return mode, None
        return mode, caps

    return mode, None


def check_reference_input_support(
    provider_id: str,
    model: str,
    capabilities: Optional[VideoGenerationProviderCapabilities],
    input_image_count: int = 0,
    input_video_count: int = 0,
    input_audio_count: int = 0,
) -> Optional[str]:
    """
    Check if a provider/model supports the requested reference inputs.
    Returns None if OK, or an error message string if not supported.

    This is the GUARD that prevents silent dropping of reference assets.
    Hermes currently has no equivalent — it just sends assets to the
    provider and hopes for the best.
    """
    mode, caps = resolve_mode_capabilities(
        capabilities, model, input_image_count, input_video_count
    )
    label = f"{provider_id}/{model}"

    if mode is None:
        return f"{label} does not support combined image/video reference inputs; skipping to avoid silent reference drop"

    if caps is None:
        if input_image_count > 0 or input_video_count > 0:
            visual = ("combined image/video reference inputs" if input_image_count > 0 and input_video_count > 0
                      else "reference image inputs" if input_image_count > 0
                      else "reference video inputs")
            return f"{label} does not support {visual}; skipping to avoid silent reference drop"
        return None

    if not getattr(caps, 'enabled', False):
        if input_image_count > 0 or input_video_count > 0:
            visual = ("combined image/video reference inputs" if input_image_count > 0 and input_video_count > 0
                      else "reference image inputs" if input_image_count > 0
                      else "reference video inputs")
            return f"{label} does not support {visual}; skipping to avoid silent reference drop"
        return None

    # Check max input images
    if input_image_count > 0:
        max_images = getattr(caps, 'maxInputImages', 0) or 0
        if input_image_count > max_images:
            if max_images == 0:
                return f"{label} does not support reference image inputs; skipping to avoid silent image drop"
            return f"{label} supports at most {max_images} reference image(s), {input_image_count} requested; skipping"

    # Check max input videos
    if input_video_count > 0:
        max_videos = getattr(caps, 'maxInputVideos', 0) or 0
        if input_video_count > max_videos:
            if max_videos == 0:
                return f"{label} does not support reference video inputs; skipping to avoid silent video drop"
            return f"{label} supports at most {max_videos} reference video(s), {input_video_count} requested; skipping"

    # Check max input audios
    if input_audio_count > 0:
        max_audios = getattr(caps, 'maxInputAudios', 0) or 0
        if input_audio_count > max_audios:
            if max_audios == 0:
                return f"{label} does not support reference audio inputs; skipping to avoid silent audio drop"
            return f"{label} supports at most {max_audios} reference audio(s), {input_audio_count} requested; skipping"

    return None
