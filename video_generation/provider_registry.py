"""
provider_registry.py — Video generation provider registry.

Adapted from OpenClaw src/video-generation/provider-registry.ts.

Manages a registry of video generation providers with alias support.
Hermes has video_gen_registry.py with a different structure; this
adds alias resolution and safer provider ID handling.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from video_types import VideoGenerationProviderCapabilities

logger = logging.getLogger(__name__)

# Blocked provider IDs (prototype pollution safety)
_UNSAFE_IDS: Set[str] = {"__proto__", "constructor", "prototype"}


@dataclass
class VideoGenerationProvider:
    """A video generation provider plugin."""
    id: str
    label: str
    capabilities: VideoGenerationProviderCapabilities
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    baseUrl: str = ""
    apiKeyEnv: str = ""
    models: List[str] = field(default_factory=list)
    defaultModel: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class VideoGenerationRegistry:
    """
    Registry of video generation providers with alias resolution.

    Supports:
    - Canonical provider lookup by ID
    - Alias resolution (e.g., "fal" → "fal-ai")
    - Safe ID validation (blocks prototype pollution)
    """

    def __init__(self):
        self._canonical: Dict[str, VideoGenerationProvider] = {}
        self._aliases: Dict[str, VideoGenerationProvider] = {}

    def register(self, provider: VideoGenerationProvider) -> None:
        """Register a provider with all its aliases."""
        pid = self._normalize_id(provider.id)
        if not pid or pid in _UNSAFE_IDS:
            logger.warning(f"Skipping unsafe provider ID: {provider.id}")
            return

        self._canonical[pid] = provider
        self._aliases[pid] = provider

        for alias in provider.aliases:
            alias_id = self._normalize_id(alias)
            if alias_id and alias_id not in _UNSAFE_IDS:
                self._aliases[alias_id] = provider

    def get(self, provider_id: str) -> Optional[VideoGenerationProvider]:
        """Look up a provider by ID or alias."""
        normalized = self._normalize_id(provider_id)
        if not normalized:
            return None
        return self._aliases.get(normalized)

    def get_canonical(self, provider_id: str) -> Optional[VideoGenerationProvider]:
        """Look up a provider by canonical ID only (no aliases)."""
        normalized = self._normalize_id(provider_id)
        if not normalized:
            return None
        return self._canonical.get(normalized)

    def list_providers(self) -> List[VideoGenerationProvider]:
        """List all registered providers (canonical only)."""
        return list(self._canonical.values())

    def list_ids(self) -> List[str]:
        """List all canonical provider IDs."""
        return list(self._canonical.keys())

    def list_all_ids(self) -> List[str]:
        """List all IDs including aliases."""
        return list(self._aliases.keys())

    @staticmethod
    def _normalize_id(provider_id: str) -> Optional[str]:
        """Normalize a provider ID for safe lookup."""
        if not provider_id:
            return None
        normalized = provider_id.strip().lower()
        if not normalized or normalized in _UNSAFE_IDS:
            return None
        return normalized


# ── Default registry with built-in providers ────────────────────────────────

_default_registry = VideoGenerationRegistry()


def get_default_registry() -> VideoGenerationRegistry:
    """Get the default global registry."""
    return _default_registry


def register_provider(provider: VideoGenerationProvider) -> None:
    """Register a provider in the default registry."""
    _default_registry.register(provider)


def get_provider(provider_id: str) -> Optional[VideoGenerationProvider]:
    """Look up a provider in the default registry."""
    return _default_registry.get(provider_id)


def list_providers() -> List[VideoGenerationProvider]:
    """List all providers in the default registry."""
    return _default_registry.list_providers()
