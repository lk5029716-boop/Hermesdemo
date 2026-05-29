"""Deterministic free port block allocation for tests.

Ported from OpenClaw src/test-utils/ports.ts

Allocates deterministic per-worker port blocks to avoid EADDRINUSE
collisions when running tests in parallel.
"""

from __future__ import annotations

import socket
from pathlib import Path


def _is_port_free(port: int) -> bool:
    """Check if a TCP port is free on 127.0.0.1."""
    if not (isinstance(port, int) and 0 < port <= 65535):
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            s.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False


def _get_os_free_port() -> int:
    """Ask the OS for a free ephemeral port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


_next_test_port_offset = 0


async def get_deterministic_free_port_block(
    offsets: list[int] | None = None,
) -> int:
    """Allocate a deterministic per-worker port block.

    Each call returns a base port such that base + offset is free
    for all requested offsets. This prevents parallel test workers
    from colliding on derived ports (e.g. gateway +1/+2/+3).

    Args:
        offsets: List of port offsets to check (default: [0, 1, 2, 3, 4])

    Returns:
        Base port number where all base+offset ports are free.

    Raises:
        RuntimeError: If no free block can be found after scanning.
    """
    global _next_test_port_offset

    offsets = offsets or [0, 1, 2, 3, 4]
    max_offset = max(offsets)
    worker_id = _get_worker_id()
    shard = abs(hash(str(worker_id))) + abs(hash(str(id(offsets))))
    range_size = 1000
    shard_count = 35
    base = 30_000 + (shard % shard_count) * range_size
    usable = range_size - max_offset
    block_size = max(max_offset + 1, 8)

    for attempt in range(0, usable, block_size):
        start = base + ((_next_test_port_offset + attempt) % usable)
        if all(_is_port_free(start + offset) for offset in offsets):
            _next_test_port_offset = (_next_test_port_offset + attempt + block_size) % usable
            return start

    # Fallback: let the OS pick
    for _ in range(25):
        port = _get_os_free_port()
        if all(_is_port_free(port + offset) for offset in offsets):
            return port

    raise RuntimeError("Failed to acquire a free port block")


def _get_worker_id() -> str:
    """Get the current test worker ID from environment."""
    import os
    return (
        os.environ.get("PYTEST_XDIST_WORKER")
        or os.environ.get("VITEST_WORKER_ID")
        or os.environ.get("VITEST_POOL_ID")
        or str(os.getpid())
    )


async def get_free_port_block_with_permission_fallback(
    offsets: list[int],
    fallback_base: int,
) -> int:
    """Get a free port block, falling back to pid-based allocation on permission errors."""
    try:
        return await get_deterministic_free_port_block(offsets)
    except PermissionError:
        import os
        return fallback_base + (os.getpid() % 10_000)
