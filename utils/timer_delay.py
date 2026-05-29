"""
timer_delay.py — Safe timer utilities.

Adapted from OpenClaw src/utils/timer-delay.ts.

Provides delay/timeout utilities that avoid event-loop starvation.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator


async def safe_delay(seconds: float) -> None:
    """
    Delay that yields to the event loop.
    Unlike time.sleep(), this doesn't block other coroutines.
    """
    if seconds <= 0:
        return
    await asyncio.sleep(seconds)


async def delayed_iterate(
    items: list,
    delay_seconds: float = 0,
) -> AsyncIterator:
    """
    Iterate over items with a可选 delay between each.
    Useful for rate-limiting API calls.
    """
    for item in items:
        yield item
        if delay_seconds > 0:
            await safe_delay(delay_seconds)


async def timeout_guard(
    coroutine,
    timeout_seconds: float,
    message: str = "Operation timed out",
) -> None:
    """Run a coroutine with a timeout, raising TimeoutError if exceeded."""
    try:
        await asyncio.wait_for(coroutine, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(message)
