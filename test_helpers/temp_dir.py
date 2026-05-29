"""Advanced temp dir helpers with async/sync variants and reference counting.

Ported from OpenClaw src/test-helpers/temp-dir.ts

Provides:
    - with_temp_dir: async temp dir with prefix, parentDir, subdir support
    - with_temp_dir_sync: sync variant
    - create_suite_temp_root_tracker: managed temp root for test suites
"""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class _PrefixRootState:
    path: str
    active_count: int = 0


_async_prefix_roots: dict[str, _PrefixRootState] = {}
_sync_prefix_roots: dict[str, _PrefixRootState] = {}
_async_dir_index = 0
_sync_dir_index = 0


def _get_root_key(prefix: str, parent_dir: str | None = None) -> str:
    return f"{parent_dir or tempfile.gettempdir()}\0{prefix}"


def _acquire_async_prefix_root(prefix: str, parent_dir: str | None = None) -> _PrefixRootState:
    global _async_prefix_roots
    key = _get_root_key(prefix, parent_dir)
    cached = _async_prefix_roots.get(key)
    if cached:
        cached.active_count += 1
        return cached
    root = tempfile.mkdtemp(prefix=prefix, dir=parent_dir)
    state = _PrefixRootState(path=root, active_count=1)
    _async_prefix_roots[key] = state
    return state


def _acquire_sync_prefix_root(prefix: str, parent_dir: str | None = None) -> _PrefixRootState:
    global _sync_prefix_roots
    key = _get_root_key(prefix, parent_dir)
    cached = _sync_prefix_roots.get(key)
    if cached:
        cached.active_count += 1
        return cached
    root = tempfile.mkdtemp(prefix=prefix, dir=parent_dir)
    state = _PrefixRootState(path=root, active_count=1)
    _sync_prefix_roots[key] = state
    return state


async def _release_async_prefix_root(prefix: str, parent_dir: str | None = None) -> None:
    global _async_prefix_roots
    key = _get_root_key(prefix, parent_dir)
    state = _async_prefix_roots.get(key)
    if not state:
        return
    state.active_count -= 1
    if state.active_count > 0:
        return
    del _async_prefix_roots[key]
    shutil.rmtree(state.path, ignore_errors=True)


def _release_sync_prefix_root(prefix: str, parent_dir: str | None = None) -> None:
    global _sync_prefix_roots
    key = _get_root_key(prefix, parent_dir)
    state = _sync_prefix_roots.get(key)
    if not state:
        return
    state.active_count -= 1
    if state.active_count > 0:
        return
    del _sync_prefix_roots[key]
async def with_temp_dir(
    prefix: str = "tmp-",
    parent_dir: str | None = None,
    subdir: str | None = None,
    *,
    run: Any = None,
) -> T:
    """Create a temp directory, run a function, then clean up.

    Args:
        prefix: Temp dir name prefix
        parent_dir: Parent directory (defaults to system temp)
        subdir: Optional subdirectory to create inside the temp dir
        run: Async function receiving the temp dir path

    Reference-counted: the root prefix dir is removed only when all
        callers using the same prefix have finished.
    """
    global _async_dir_index
    root = _acquire_async_prefix_root(prefix, parent_dir)
    base = os.path.join(root.path, f"dir-{_async_dir_index}")
    _async_dir_index += 1
    os.makedirs(base, exist_ok=True)
    dir_path = os.path.join(base, subdir) if subdir else base
    if subdir:
        os.makedirs(dir_path, exist_ok=True)
    try:
        return await run(dir_path)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        await _release_async_prefix_root(prefix, parent_dir)


def with_temp_dir_sync(
    prefix: str = "tmp-",
    parent_dir: str | None = None,
    subdir: str | None = None,
    *,
    run: Any = None,
) -> T:
    """Synchronous variant of with_temp_dir."""
    global _sync_dir_index
    root = _acquire_sync_prefix_root(prefix, parent_dir)
    base = os.path.join(root.path, f"dir-{_sync_dir_index}")
    _sync_dir_index += 1
    os.makedirs(base, exist_ok=True)
    dir_path = os.path.join(base, subdir) if subdir else base
    if subdir:
        os.makedirs(dir_path, exist_ok=True)
    try:
        return run(dir_path)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        _release_sync_prefix_root(prefix, parent_dir)


def create_suite_temp_root_tracker(
    prefix: str = "suite-",
    parent_dir: str | None = None,
) -> "SuiteTempRootTracker":
    """Create a managed temp root for test suites.

    Returns an object with setup(), make(), and cleanup() methods.
    """
    return SuiteTempRootTracker(prefix=prefix, parent_dir=parent_dir)


@dataclass
class SuiteTempRootTracker:
    prefix: str
    parent_dir: str | None = None
    _root: str = ""
    _next_index: int = 0

    async def setup(self) -> str:
        self._root = tempfile.mkdtemp(prefix=self.prefix, dir=self.parent_dir)
        self._next_index = 0
        return self._root

    async def make(self, prefix: str = "case") -> str:
        dir_path = os.path.join(self._root, f"{prefix}-{self._next_index}")
        self._next_index += 1
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    async def cleanup(self) -> None:
        if self._root:
            root = self._root
            self._root = ""
            self._next_index = 0
            shutil.rmtree(root, ignore_errors=True)
