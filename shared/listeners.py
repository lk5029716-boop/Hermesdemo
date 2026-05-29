"""Listener notification utility.

Ported from OpenClaw src/shared/listeners.ts
"""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def notify_listeners(
    listeners: list[Callable[[T], None]],
    event: T,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """Notify all listeners of an event, catching and optionally reporting errors."""
    for listener in listeners:
        try:
            listener(event)
        except Exception as e:
            if on_error:
                on_error(e)


def register_listener(
    listeners: set[Callable[[T], None]],
    listener: Callable[[T], None],
) -> Callable[[], None]:
    """Register a listener. Returns an unsubscribe function."""
    listeners.add(listener)
    return lambda: listeners.discard(listener)
