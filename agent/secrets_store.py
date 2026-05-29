"""
Structured secrets storage for Hermes.

Stores secrets (API keys, tokens) as JSON on disk with CRUD operations.
Replaces plain-text .env dumping with a proper secrets API.

Based on OpenHands secrets/ folder pattern.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SECRETS_FILE_NAME = "secrets.json"


class SecretStr:
    """String that masks its value in logs/repr."""

    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        if not self._value:
            return "SecretStr('')"
        if len(self._value) <= 4:
            return "SecretStr('****')"
        return f"SecretStr('{self._value[:2]}****')"

    def __str__(self) -> str:
        return self.__repr__()

    def __bool__(self) -> bool:
        return bool(self._value)


class SecretsStore:
    """JSON-backed secrets storage with CRUD operations.

    Stores secrets in ~/.hermes/secrets.json.
    Provider tokens and custom user secrets are supported.
    """

    def __init__(self, hermes_home: Optional[Path] = None) -> None:
        if hermes_home is None:
            from hermes_constants import get_hermes_home
            hermes_home = get_hermes_home()
        self._home = Path(hermes_home)
        self._secrets_file = self._home / _SECRETS_FILE_NAME
        self._data: Dict[str, Any] = self._load()

    # -- persistence ---------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        if self._secrets_file.exists():
            try:
                return json.loads(self._secrets_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("secrets: could not load %s: %s", self._secrets_file, exc)
        return {"providers": {}, "custom": {}}

    def _save(self) -> None:
        self._home.mkdir(parents=True, exist_ok=True)
        # Atomic write: write to temp, then rename
        tmp = self._secrets_file.with_suffix(".tmp")
        try:
            tmp.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self._secrets_file)
        except Exception as exc:
            logger.warning("secrets: could not save %s: %s", self._secrets_file, exc)

    # -- provider tokens -----------------------------------------------------

    def get_provider_token(self, provider: str) -> Optional[SecretStr]:
        """Get a stored provider token."""
        value = self._data.get("providers", {}).get(provider)
        return SecretStr(value) if value else None

    def set_provider_token(self, provider: str, token: str) -> None:
        """Store a provider token."""
        self._data.setdefault("providers", {})[provider] = token
        self._save()
        logger.info("secrets: stored provider token for %s", provider)

    def remove_provider_token(self, provider: str) -> bool:
        """Remove a provider token. Returns True if it existed."""
        providers = self._data.get("providers", {})
        if provider in providers:
            del providers[provider]
            self._save()
            logger.info("secrets: removed provider token for %s", provider)
            return True
        return False

    def list_providers(self) -> List[str]:
        """List all providers with stored tokens."""
        return list(self._data.get("providers", {}).keys())

    # -- custom secrets ------------------------------------------------------

    def get_custom_secret(self, key: str) -> Optional[SecretStr]:
        """Get a custom user secret."""
        value = self._data.get("custom", {}).get(key)
        return SecretStr(value) if value else None

    def set_custom_secret(self, key: str, value: str) -> None:
        """Store a custom user secret."""
        self._data.setdefault("custom", {})[key] = value
        self._save()
        logger.info("secrets: stored custom secret '%s'", key)

    def remove_custom_secret(self, key: str) -> bool:
        """Remove a custom secret. Returns True if it existed."""
        custom = self._data.get("custom", {})
        if key in custom:
            del custom[key]
            self._save()
            logger.info("secrets: removed custom secret '%s'", key)
            return True
        return False

    def list_custom_secrets(self) -> List[str]:
        """List all custom secret keys."""
        return list(self._data.get("custom", {}).keys())

    # -- export (safe) -------------------------------------------------------

    def export_safe(self) -> Dict[str, Any]:
        """Export secrets with masked values (for display)."""
        result: Dict[str, Any] = {"providers": {}, "custom": {}}
        for k, v in self._data.get("providers", {}).items():
            result["providers"][k] = repr(SecretStr(str(v)))
        for k, v in self._data.get("custom", {}).items():
            result["custom"][k] = repr(SecretStr(str(v)))
        return result
