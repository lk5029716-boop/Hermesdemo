"""
wizard_secret.py — Secret input resolution during setup.

Adapted from OpenClaw src/wizard/setup.secret-input.ts.

Resolves SecretRef references and normalizes secret input values.
Hermes has credential_files.py and env var handling, but lacks
the structured SecretRef resolution during interactive setup.
"""

from __future__ import annotations

import os
from typing import Any, Optional


class SecretRef:
    """Reference to a secret stored outside plaintext config."""
    def __init__(self, source: str, provider: str, id: str):
        self.source = source
        self.provider = provider
        self.id = id

    def __str__(self) -> str:
        return f"{self.source}:{self.provider}:{self.id}"


class SecretResolver:
    """Resolves secret references during setup wizard."""

    def __init__(self, config: dict, env: dict | None = None):
        self.config = config
        self.env = env or dict(os.environ)
        self.defaults = config.get("secrets", {}).get("defaults", {}) if isinstance(config.get("secrets"), dict) else {}

    def resolve_secret_input(self, value: Any, path: str) -> Optional[str]:
        """
        Resolve a secret input value:
        - If it's a SecretRef dict, resolve it
        - If it's a plaintext string, normalize and return
        - If empty/None, return None
        """
        ref = self._resolve_ref(value)
        if ref:
            try:
                return self._resolve_ref_string(ref)
            except Exception as e:
                raise ValueError(
                    f"{path}: failed to resolve SecretRef '{ref}': {e}"
                ) from e

        return self._normalize_plaintext(value)

    def _resolve_ref(self, value: Any) -> Optional[str]:
        """Check if value is a SecretRef and return its string representation."""
        if isinstance(value, SecretRef):
            return str(value)
        if isinstance(value, dict):
            ref_source = value.get("source")
            ref_provider = value.get("provider")
            ref_id = value.get("id")
            if ref_source and ref_provider and ref_id:
                return f"{ref_source}:{ref_provider}:{ref_id}"
            # Check with $ref key
            if "$ref" in value:
                return value["$ref"]
        return None

    def _resolve_ref_string(self, ref: str) -> str:
        """
        Resolve a SecretRef string (source:provider:id).

        Supported sources:
        - env: read from environment variable
        - file: read from file path
        - exec: execute a command and read stdout
        - secret: read from config secrets store
        """
        parts = ref.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid SecretRef format: {ref}")

        source, provider, id_val = parts

        if source == "env":
            # provider is the env var name, id is unused
            val = self.env.get(provider)
            if val is None:
                raise ValueError(f"Environment variable {provider} not set")
            return val

        if source == "file":
            # provider is the file path
            from pathlib import Path
            p = Path(provider).expanduser()
            if not p.exists():
                raise ValueError(f"Secret file not found: {p}")
            return p.read_text().strip()

        if source == "exec":
            # provider is a command template, id is the argument
            import subprocess
            cmd = f"{provider} {id_val}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                raise ValueError(f"Exec failed: {result.stderr}")
            return result.stdout.strip()

        if source == "secret":
            # Look in config secrets store
            secrets = self.config.get("secrets", {})
            store = secrets.get("store", {}) if isinstance(secrets, dict) else {}
            if isinstance(store, dict):
                val = store.get(id_val)
                if val:
                    return str(val)

            raise ValueError(f"Secret '{id_val}' not found in config store")

        raise ValueError(f"Unsupported SecretRef source: {source}")

    def _normalize_plaintext(self, value: Any) -> Optional[str]:
        """Normalize a plaintext value, returning None for empty."""
        if value is None:
            return None
        s = str(value)
        # Strip pasted bracketed markers
        import re
        s = re.sub(r"\x1b\[\s*200~|\x1b\[\s*201~", "", s)
        s = s.strip()
        return s if s else None

    def resolve_with_defaults(self, value: Any, field_name: str) -> Optional[str]:
        """Resolve a value, falling back to defaults from config."""
        result = self.resolve_secret_input(value, field_name)
        if result is not None:
            return result

        # Check defaults
        if isinstance(self.defaults, dict):
            default = self.defaults.get(field_name)
            if default:
                return str(default)

        return None
