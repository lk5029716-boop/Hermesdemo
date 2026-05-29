"""
openai_tts_provider.py — Generic OpenAI-compatible TTS provider adapter.

Adapted from OpenClaw src/tts/openai-compatible-speech-provider.ts.

Provides a reusable adapter for any OpenAI-compatible TTS endpoint.
OpenAI, ElevenLabs-compatible, and many local TTS servers use the
same /v1/audio/speech API shape.

Hermes has tts_tool.py but it handles each provider separately.
This gives a single adapter that works with any compatible endpoint.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TtsProviderOptions:
    """Options for a TTS provider request."""
    model: str = "tts-1"
    voice: str = "alloy"
    input_text: str = ""
    response_format: str = "mp3"  # mp3, opus, aac, flac, wav, pcm
    speed: float = 1.0
    language: str | None = None
    instructions: str | None = None  # For gpt-4o-mini-tts style providers
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TtsAudioResult:
    """Result of a TTS generation request."""
    audio_data: bytes
    content_type: str = "audio/mp3"
    format: str = "mp3"


class OpenAiCompatibleTtsProvider:
    """
    Generic adapter for OpenAI-compatible TTS endpoints.

    Works with:
    - OpenAI (api.openai.com)
    - Local TTS servers (OpenVoice, XTTS, etc.)
    - ElevenLabs-compatible endpoints
    - Any server implementing POST /v1/audio/speech
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "tts-1",
        default_voice: str = "alloy",
        timeout_seconds: float = 30.0,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._default_voice = default_voice
        self._timeout = timeout_seconds

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        speed: float | None = None,
        language: str | None = None,
        instructions: str | None = None,
        response_format: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> TtsAudioResult:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            model: TTS model ID
            voice: Voice name
            speed: Speech speed (0.25-4.0 for OpenAI)
            language: Language code (some providers)
            instructions: Voice instructions (gpt-4o-mini-tts style)
            response_format: Output format (mp3, wav, etc.)
            extra: Extra provider-specific options

        Returns:
            TtsAudioResult with audio data

        Raises:
            TtsError on failure
        """
        if not text or not text.strip():
            return TtsAudioResult(audio_data=b"", content_type="audio/mp3")

        options = TtsProviderOptions(
            model=model or self._default_model,
            voice=voice or self._default_voice,
            input_text=text,
            response_format=response_format or "mp3",
            speed=speed if speed is not None else 1.0,
            language=language,
            instructions=instructions,
            extra=extra or {},
        )

        return await self._make_request(options)

    async def _make_request(self, options: TtsProviderOptions) -> TtsAudioResult:
        """Make the actual HTTP request to the TTS endpoint."""
        import urllib.request
        import urllib.error
        import json

        url = f"{self._base_url}/audio/speech"
        payload = {
            "model": options.model,
            "input": options.input_text,
            "voice": options.voice,
            "response_format": options.response_format,
        }

        # Speed only applies to some providers
        if options.speed != 1.0:
            payload["speed"] = max(0.25, min(4.0, options.speed))

        # Provider-specific options
        if options.language:
            payload["language"] = options.language
        if options.instructions:
            payload["instructions"] = options.instructions
        if options.extra:
            payload.update(options.extra)

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            response = urllib.request.urlopen(req, timeout=self._timeout)
            audio_data = response.read()
            content_type = response.headers.get("Content-Type", "audio/mp3")
            fmt = options.response_format
            return TtsAudioResult(
                audio_data=audio_data,
                content_type=content_type,
                format=fmt,
            )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            logger.error(f"TTS HTTP error {e.code}: {error_body}")
            raise TtsError(f"TTS request failed: {e.code} {e.reason}") from e
        except Exception as e:
            logger.error(f"TTS request error: {e}")
            raise TtsError(f"TTS request failed: {e}") from e

    async def list_voices(self) -> list[dict[str, Any]]:
        """List available voices (if the endpoint supports it)."""
        import urllib.request
        import urllib.error
        import json

        url = f"{self._base_url}/audio/voices"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        req = urllib.request.Request(url, headers=headers)

        try:
            response = urllib.request.urlopen(req, timeout=self._timeout)
            data = json.loads(response.read().decode("utf-8"))
            return data.get("voices", data if isinstance(data, list) else [])
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("TTS endpoint does not support /audio/voices")
                return []
            raise TtsError(f"Failed to list voices: {e.code}") from e


class TtsError(Exception):
    """TTS generation error."""
    pass
