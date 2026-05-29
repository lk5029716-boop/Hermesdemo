"""Detached task lifecycle runtime registration.

Ported from OpenClaw src/tasks/detached-task-runtime-state.ts
"""

from __future__ import annotations

from .detached_contract import DetachedTaskLifecycleRuntime, DetachedTaskLifecycleRuntimeRegistration


_registration: DetachedTaskLifecycleRuntimeRegistration | None = None


def register_detached_task_lifecycle_runtime(
    plugin_id: str,
    runtime: DetachedTaskLifecycleRuntime,
) -> None:
    """Register a detached task lifecycle runtime for a plugin."""
    global _registration
    _registration = DetachedTaskLifecycleRuntimeRegistration(
        plugin_id=plugin_id,
        runtime=runtime,
    )


def get_detached_task_lifecycle_runtime_registration() -> DetachedTaskLifecycleRuntimeRegistration | None:
    """Get the current registration, or None."""
    if _registration is None:
        return None
    return DetachedTaskLifecycleRuntimeRegistration(
        plugin_id=_registration.plugin_id,
        runtime=_registration.runtime,
    )


def get_registered_detached_task_lifecycle_runtime() -> DetachedTaskLifecycleRuntime | None:
    """Get the registered runtime, or None."""
    return _registration.runtime if _registration else None


def clear_detached_task_lifecycle_runtime_registration() -> None:
    """Clear the registration."""
    global _registration
    _registration = None
