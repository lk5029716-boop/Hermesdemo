"""
queue_helpers.py — Async queue with drop policies.

Adapted from OpenClaw src/utils/queue-helpers.ts.

Multi-producer/multi-consumer async queue with:
- Backpressure (maxsize)
- Drop policies (oldest, newest, reject)
- Drain support
- Stats tracking

Useful when producers are faster than consumers (message ingestion,
API result collection, etc.).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DropPolicy(str, Enum):
    """What to do when queue is full."""
    OLDEST = "oldest"    # Drop oldest item to make room
    NEWEST = "newest"    # Drop the item being added (reject)
    REJECT = "reject"    # Raise QueueFull


class QueueFull(Exception):
    """Raised when queue is full and policy is REJECT."""
    pass


@dataclass
class QueueStats:
    """Queue statistics."""
    enqueued: int = 0
    dequeued: int = 0
    dropped_oldest: int = 0
    dropped_newest: int = 0
    rejected: int = 0
    drained: int = 0


@dataclass
class QueueConfig:
    """Queue configuration."""
    maxsize: int = 0          # 0 = unlimited
    drop_policy: DropPolicy = DropPolicy.OLDEST


class AsyncDropQueue(Generic[T]):
    """
    Async queue with drop policies for backpressure handling.

    Unlike asyncio.Queue, this never blocks producers — it drops
    according to the configured policy when full.
    """

    def __init__(self, config: QueueConfig | None = None):
        self._config = config or QueueConfig()
        self._queue: asyncio.Queue[T] = asyncio.Queue(
            maxsize=self._config.maxsize
        )
        self._stats = QueueStats()

    @property
    def stats(self) -> QueueStats:
        return self._stats

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def empty(self) -> bool:
        return self._queue.empty()

    @property
    def full(self) -> bool:
        return self._queue.full()

    async def put(self, item: T) -> bool:
        """
        Put an item. Returns True if item was queued.
        Returns False or drops according to policy if full.
        """
        if not self._queue.full():
            await self._queue.put(item)
            self._stats.enqueued += 1
            return True

        policy = self._config.drop_policy
        if policy == DropPolicy.REJECT:
            self._stats.rejected += 1
            raise QueueFull("Queue is full")

        if policy == DropPolicy.NEWEST:
            self._stats.dropped_newest += 1
            return False

        # OLDEST: drop oldest to make room
        try:
            self._queue.get_nowait()
            self._stats.dropped_oldest += 1
        except asyncio.QueueEmpty:
            pass

        try:
            self._queue.put_nowait(item)
            self._stats.enqueued += 1
            return True
        except asyncio.QueueFull:
            self._stats.rejected += 1
            return False

    def put_nowait(self, item: T) -> bool:
        """Non-blocking put. Returns True if item was queued."""
        if not self._queue.full():
            try:
                self._queue.put_nowait(item)
                self._stats.enqueued += 1
                return True
            except asyncio.QueueFull:
                pass

        policy = self._config.drop_policy
        if policy == DropPolicy.REJECT:
            self._stats.rejected += 1
            raise QueueFull("Queue is full")

        if policy == DropPolicy.NEWEST:
            self._stats.dropped_newest += 1
            return False

        try:
            self._queue.get_nowait()
            self._stats.dropped_oldest += 1
        except asyncio.QueueEmpty:
            pass

        try:
            self._queue.put_nowait(item)
            self._stats.enqueued += 1
            return True
        except asyncio.QueueFull:
            self._stats.rejected += 1
            return False

    async def get(self) -> T:
        """Get an item, waiting if necessary."""
        item = await self._queue.get()
        self._stats.dequeued += 1
        return item

    def get_nowait(self) -> T:
        """Non-blocking get."""
        item = self._queue.get_nowait()
        self._stats.dequeued += 1
        return item

    async def drain(self) -> list[T]:
        """Drain all items from the queue."""
        items: list[T] = []
        while not self._queue.empty():
            try:
                items.append(self._queue.get_nowait())
                self._stats.dequeued += 1
            except asyncio.QueueEmpty:
                break
        self._stats.drained += len(items)
        return items

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()

    def close(self) -> None:
        """Signal that no more items will be added."""
        pass  # Compatibility with OpenClaw's richer close semantics

    def __len__(self) -> int:
        return self.qsize

    def __bool__(self) -> bool:
        return not self.empty
