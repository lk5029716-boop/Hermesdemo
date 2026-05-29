"""
video_types.py — Core video generation types.

Adapted from OpenClaw src/video-generation/types.ts.

Defines the type system for video generation: modes, capabilities,
requests, results, assets. Hermes has basic video types; this is
a more structured approach with per-model capability overlays.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class VideoGenerationMode(str, Enum):
    """What kind of video generation operation."""
    GENERATE = "generate"          # Text-to-video
    IMAGE_TO_VIDEO = "imageToVideo"  # Image (first frame) to video
    VIDEO_TO_VIDEO = "videoToVideo"  # Video transform / remix


class VideoResolution(str, Enum):
    """Standard video resolutions. Maps to size at 16:9."""
    P360 = "360P"
    P480 = "480P"
    P540 = "540P"
    P720 = "720P"
    P768 = "768P"
    P1080 = "1080P"


# Resolution order for closest-match snapping
VIDEO_RESOLUTION_ORDER: List[VideoResolution] = [
    VideoResolution.P360,
    VideoResolution.P480,
    VideoResolution.P540,
    VideoResolution.P720,
    VideoResolution.P768,
    VideoResolution.P1080,
]

# Default sizes for resolutions (width*height at 16:9)
DEFAULT_RESOLUTION_TO_SIZE: Dict[str, str] = {
    "480P": "832*480",
    "720P": "1280*720",
    "1080P": "1920*1080",
}


@dataclass
class VideoGenerationModeCapabilities:
    """Capabilities for a specific generation mode."""
    maxVideos: int = 1
    maxDurationSeconds: Optional[int] = None
    supportedDurationSeconds: Optional[List[int]] = None
    supportsSize: bool = False
    supportsAspectRatio: bool = False
    supportsResolution: bool = False
    supportsAudio: bool = False
    supportsWatermark: bool = False
    supportedDurationSecondsByModel: Optional[Dict[str, List[int]]] = None
    providerOptions: Optional[Dict[str, Any]] = None


@dataclass
class VideoGenerationTransformCapabilities(VideoGenerationModeCapabilities):
    """Capabilities for transform modes (imageToVideo, videoToVideo)."""
    enabled: bool = False
    maxInputImages: int = 0
    maxInputVideos: int = 0
    maxInputAudios: int = 0
    maxInputImagesByModel: Optional[Dict[str, int]] = None
    maxInputVideosByModel: Optional[Dict[str, int]] = None
    maxInputAudiosByModel: Optional[Dict[str, int]] = None
    aspectRatios: Optional[List[str]] = None
    resolutions: Optional[List[str]] = None
    sizes: Optional[List[str]] = None


@dataclass
class VideoGenerationProviderCapabilities:
    """Full capability set for a video generation provider."""
    generate: Optional[VideoGenerationModeCapabilities] = None
    imageToVideo: Optional[VideoGenerationTransformCapabilities] = None
    videoToVideo: Optional[VideoGenerationTransformCapabilities] = None
    maxInputImages: int = 0
    maxInputVideos: int = 0
    maxInputAudios: int = 0
    providerOptions: Optional[Dict[str, Any]] = None


@dataclass
class VideoGenerationSourceAsset:
    """Input reference asset (image, video, audio)."""
    url: Optional[str] = None
    buffer: Optional[bytes] = None
    mimeType: Optional[str] = None
    fileName: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedVideoAsset:
    """Output video asset."""
    url: Optional[str] = None
    buffer: Optional[bytes] = None
    mimeType: str = "video/mp4"
    fileName: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoIgnoredOverride:
    """An override that was dropped because the provider doesn't support it."""
    key: str
    value: Any


@dataclass
class VideoNormalizationEntry:
    """A normalization that was applied to an override."""
    requested: Any
    applied: Any
    derivedFrom: Optional[str] = None
    supportedValues: Optional[List[Any]] = None


@dataclass
class VideoGenerationNormalization:
    """Summary of all normalizations applied."""
    size: Optional[VideoNormalizationEntry] = None
    aspectRatio: Optional[VideoNormalizationEntry] = None
    resolution: Optional[VideoNormalizationEntry] = None
    durationSeconds: Optional[VideoNormalizationEntry] = None


@dataclass
class ResolvedVideoGenerationOverrides:
    """Result of resolving overrides against provider capabilities."""
    size: Optional[str] = None
    aspectRatio: Optional[str] = None
    resolution: Optional[str] = None
    seconds: Optional[int] = None
    supportedDurationSeconds: Optional[List[int]] = None
    audio: Optional[bool] = None
    watermark: Optional[bool] = None
    ignoredOverrides: List[VideoIgnoredOverride] = field(default_factory=list)
    normalization: Optional[VideoGenerationNormalization] = None
