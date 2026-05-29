"""
chunk_items.py — Batch/chunk utility.

Adapted from OpenClaw src/utils/chunk-items.ts.

Splits a list into fixed-size batches.
Generic utility — no dependencies.
"""

from __future__ import annotations

from typing import Iterator, TypeVar

T = TypeVar("T")


def chunk_items(items: list[T], size: int) -> Iterator[list[T]]:
    """Split a list into fixed-size chunks."""
    if size <= 0:
        raise ValueError(f"Chunk size must be > 0, got {size}")
    for i in range(0, len(items), size):
        yield items[i : i + size]
