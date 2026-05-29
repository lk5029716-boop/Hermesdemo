"""
run_with_concurrency.py — Concurrency limiter.

Adapted from OpenClaw src/utils/run-with-concurrency.ts.

Runs async tasks with a maximum concurrency limit.
More flexible than asyncio.Semaphore — supports per-key limits.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Sequence, TypeVar

T = TypeVar("T")


async def run_with_concurrency(
    items: Sequence,
    fn: Callable[[Any], Awaitable[T]],
    limit: int = 5,
    key_fn: Callable[[Any], str] | None = None,
) -> list[T]:
    """
    Run async tasks with a maximum concurrency limit.

    Args:
        items: Items to process
        fn: Async function to call per item
        limit: Max concurrent tasks
        key_fn: Optional key function for per-key limits

    Returns:
        List of results in original order
    """
    if key_fn:
        return await _run_with_key_concurrency(items, fn, limit, key_fn)

    semaphore = asyncio.Semaphore(limit)
    ordered: list[tuple[int, Any]] = list(enumerate(items))

    async def run_with_sem(idx_item: tuple[int, Any]) -> tuple[int, T]:
        idx, item = idx_item
        async with semaphore:
            result = await fn(item)
            return idx, result

    tasks = [asyncio.create_task(run_with_sem(it)) for it in ordered]
    results = await asyncio.gather(*tasks)

    # Restore original order
    results.sort(key=lambda x: x[0])
    return [r[1] for r in results]


async def _run_with_key_concurrency(
    items: Sequence,
    fn: Callable[[Any], Awaitable[T]],
    limit: int,
    key_fn: Callable[[Any], str],
) -> list[T]:
    """Per-key concurrency limit."""
    key_locks: dict[str, asyncio.Semaphore] = {}
    ordered: list[tuple[int, Any, str]] = [
        (i, item, key_fn(item)) for i, item in enumerate(items)
    ]

    async def run_locked(args: tuple[int, Any, str]) -> tuple[int, T]:
        idx, item, key = args
        lock = key_locks.setdefault(key, asyncio.Semaphore(limit))
        async with lock:
            result = await fn(item)
            return idx, result

    tasks = [asyncio.create_task(run_locked(it)) for it in ordered]
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x[0])
    return [r[1] for r in results]
