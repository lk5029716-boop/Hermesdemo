"""Store snapshot type for task registry.

Ported from OpenClaw src/tasks/task-registry.store.types.ts
"""

from __future__ import annotations

from .types import TaskDeliveryState, TaskRecord


class TaskRegistryStoreSnapshot:
    """A point-in-time snapshot of the task registry store."""

    def __init__(self) -> None:
        self.tasks: dict[str, TaskRecord] = {}
        self.delivery_states: dict[str, TaskDeliveryState] = {}
