"""Tracked temp directory pool with cleanup.

Ported from OpenClaw src/test-utils/tracked-temp-dirs.ts
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path


def create_tracked_temp_dirs() -> "TrackedTempDirs":
    """Create a tracked temp dir manager.

    Returns an object with:
        make(prefix) → create a new tracked temp dir
        cleanup()    → remove all tracked dirs and their contents
    """

    class TrackedTempDirs:
        def __init__(self) -> None:
            self._prefix_roots: dict[str, dict[str, object]] = {}
            self._pending_prefix_roots: dict[str, object] = {}
            self._cleanup_roots: set[str] = set()
            self._global_dir_index = 0

        async def make(self, prefix: str) -> str:
            state = await self._ensure_prefix_root(prefix)
            dir_path = os.path.join(
                state["root"],  # type: ignore[typeddict-item]
                f"dir-{self._global_dir_index}",
            )
            state["next_index"] = state["next_index"] + 1  # type: ignore[typeddict-item, operator]
            self._global_dir_index += 1
            os.makedirs(dir_path, exist_ok=True)
            return dir_path

        async def cleanup(self) -> None:
            roots = list(self._cleanup_roots)
            self._pending_prefix_root.clear() if hasattr(self, '_pending_prefix_root') else None
            dirlists = await asyncio.gather(
                *[self._safe_listdir(dir_path) for dir_path in roots]
            )
            await asyncio.gather(
                *[
                    self._safe_rm(os.path.join(dir_path, entry))
                    for dir_path, entries in zip(roots, dirlists)
                    for entry in entries
                ]
            )
            for state in self._prefix_roots.values():
                state["next_index"] = 0  # type: ignore[typeddict-item]

        async def _ensure_prefix_root(self, prefix: str) -> dict[str, object]:
            if prefix in self._prefix_roots:
                return self._prefix_roots[prefix]
            if prefix in self._pending_prefix_roots:
                return await self._pending_prefix_roots[prefix]  # type: ignore[misc]

            root = tempfile.mkdtemp(prefix=prefix)
            state: dict[str, object] = {"root": root, "next_index": 0}
            self._prefix_roots[prefix] = state
            self._cleanup_roots.add(root)
            return state

        @staticmethod
        async def _safe_listdir(dir_path: str) -> list[str]:
            try:
                return os.listdir(dir_path)
            except FileNotFoundError:
                return []

        @staticmethod
        async def _safe_rm(path: str) -> None:
            import aiofiles.os
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    await aiofiles.os.remove(path)
            except Exception:
                pass

    return TrackedTempDirs()
