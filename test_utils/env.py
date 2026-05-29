"""Environment variable capture and restoration utilities.

Ported from OpenClaw src/test-utils/env.ts
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import TypeVar


def capture_env(keys: list[str]) -> dict[str, Callable[[], None]]:
    """Capture current env var values and return a restore function."""
    snapshot: dict[str, str | None] = {}
    for key in keys:
        snapshot[key] = os.environ.get(key)

    def restore() -> None:
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return {"restore": restore}


def apply_env_values(env: dict[str, str | None]) -> None:
    """Apply a dict of env var values to os.environ."""
    for key, value in env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def with_env[T](env: dict[str, str | None], fn: Callable[[], T]) -> T:
    """Run a function with temporary env var overrides, then restore."""
    snapshot = capture_env(list(env.keys()))
    try:
        apply_env_values(env)
        return fn()
    finally:
        snapshot["restore"]()


async def with_env_async[T](
    env: dict[str, str | None], fn: Callable[[], T]
) -> T:
    """Run a function with temporary env var overrides, then restore."""
    import asyncio

    snapshot = capture_env(list(env.keys()))
    try:
        apply_env_values(env)
        result = fn()
        if asyncio.iscoroutine(result):
            return await result  # type: ignore[return-value]
        return result  # type: ignore[return-value]
    finally:
        snapshot["restore"]()


def capture_full_env() -> dict[str, Callable[[], None]]:
    """Capture the entire current environment and return a restore function."""
    snapshot: dict[str, str | None] = dict(os.environ)

    def restore() -> None:
        # Remove keys not in snapshot
        to_remove = [k for k in os.environ if k not in snapshot]
        for key in to_remove:
            del os.environ[key]
        # Restore snapshotted values
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return {"restore": restore}


# Env keys used by OpenClaw path resolution
PATH_RESOLUTION_ENV_KEYS = [
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "OPENCLAW_HOME",
    "OPENCLAW_STATE_DIR",
    "OPENCLAW_BUNDLED_PLUGINS_DIR",
    "OPENCLAW_DISABLE_BUNDLED_PLUGINS",
]


def create_path_resolution_env(
    home_dir: str,
    env: dict[str, str | None] | None = None,
) -> dict[str, str | None]:
    """Create an environment dict with standard path resolution env vars set."""
    from pathlib import Path

    resolved_home = str(Path(home_dir).resolve())
    next_env: dict[str, str | None] = {
        **{k: os.environ.get(k) for k in os.environ},
        "HOME": resolved_home,
        "USERPROFILE": resolved_home,
        "OPENCLAW_HOME": None,
        "OPENCLAW_STATE_DIR": None,
        "OPENCLAW_BUNDLED_PLUGINS_DIR": None,
        "OPENCLAW_DISABLE_BUNDLED_PLUGINS": None,
    }

    # Windows HOME drive/path
    import sys
    if sys.platform == "win32":
        match = __import__("re").match(r"^([A-Za-z]:)(.*)$", resolved_home)
        if match:
            next_env["HOMEDRIVE"] = match.group(1)
            next_env["HOMEPATH"] = match.group(2) or "\\"

    if env:
        next_env.update(env)

    return next_env
