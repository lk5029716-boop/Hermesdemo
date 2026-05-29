"""
video_generation — Video generation capability negotiation layer.

Adapted from OpenClaw src/video-generation/.

Provides structured capability checking for video generation providers:
- Mode detection (text-to-video, image-to-video, video-to-video)
- Per-model capability resolution with overlays
- Reference input validation (prevents silent asset dropping)
- Duration snapping to supported values
- Override normalization (size, aspect ratio, resolution, audio, watermark)
- Provider registry with alias resolution

Hermes has plugins/video_gen/ with Fal and xAI providers, but lacks
the capability negotiation layer. This module fills that gap.
"""

from .video_types import (
    VideoGenerationMode,
    VideoResolution,
    VideoGenerationModeCapabilities,
    VideoGenerationTransformCapabilities,
    VideoGenerationProviderCapabilities,
    VideoGenerationSourceAsset,
    GeneratedVideoAsset,
    VideoIgnoredOverride,
    VideoNormalizationEntry,
    VideoGenerationNormalization,
    ResolvedVideoGenerationOverrides,
    VIDEO_RESOLUTION_ORDER,
    DEFAULT_RESOLUTION_TO_SIZE,
)
from .capabilities import (
    resolve_mode,
    list_supported_modes,
    resolve_mode_capabilities,
    check_reference_input_support,
)
from .duration_support import (
    resolve_supported_durations,
    snap_duration,
    normalize_duration,
)
from .normalization import (
    resolve_overrides,
    has_normalization,
)
from .model_ref import (
    ModelRef,
    parse_model_ref,
    resolve_model_string,
)
from .provider_registry import (
    VideoGenerationProvider,
    VideoGenerationRegistry,
    get_default_registry,
    register_provider,
    get_provider,
    list_providers,
)

__all__ = [
    # Types
    "VideoGenerationMode",
    "VideoResolution",
    "VideoGenerationModeCapabilities",
    "VideoGenerationTransformCapabilities",
    "VideoGenerationProviderCapabilities",
    "VideoGenerationSourceAsset",
    "GeneratedVideoAsset",
    "VideoIgnoredOverride",
    "VideoNormalizationEntry",
    "VideoGenerationNormalization",
    "ResolvedVideoGenerationOverrides",
    "VIDEO_RESOLUTION_ORDER",
    "DEFAULT_RESOLUTION_TO_SIZE",
    # Capabilities
    "resolve_mode",
    "list_supported_modes",
    "resolve_mode_capabilities",
    "check_reference_input_support",
    # Duration
    "resolve_supported_durations",
    "snap_duration",
    "normalize_duration",
    # Normalization
    "resolve_overrides",
    "has_normalization",
    # Model ref
    "ModelRef",
    "parse_model_ref",
    "resolve_model_string",
    # Registry
    "VideoGenerationProvider",
    "VideoGenerationRegistry",
    "get_default_registry",
    "register_provider",
    "get_provider",
    "list_providers",
]
