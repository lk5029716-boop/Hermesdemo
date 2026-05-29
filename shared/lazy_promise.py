"""Lazy promise loading utility.

Ported from OpenClaw src/shared/lazy-promise.ts
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable


class LazyPromiseLoader:
    """Loads a value lazily on first access, optionally retrying on rejection."""

    def __init__(
        self,
        factory: Callable[[], Awaitable[Any]],
        *,
        cache_rejections: bool = False,
    ) -> None:
        self._factory = factory
        self._cache_rejections = cache_rejections
        self._promise: Awaitable[Any] | None = None

    async def load(self) -> Any:
        if self._promise is not None:
            return await self._promise
        promise = self._factory()
        if not self._cache_rejections:
            original = promise

            async def _wrap() -> Any:
                try:
                    return await original
                except Exception:
                    self._promise = None
                    raise

            promise = _wrap()
        self._promise = promise
        return await promise

    def clear(self) -> None:
        self._promise = None


def create_lazy_promise_loader(
    factory: Callable[[], Awaitable[Any]],
    *,
    cache_rejections: bool = False,
) -> LazyPromiseLoader:
    return LazyPromiseLoader(factory, cache_rejections=cache_rejections)
