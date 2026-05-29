"""Task registry in-memory process state.

Ported from OpenClaw src/tasks/task-registry.process-state.ts
"""

from __future__ import annotations

from .types import TaskDeliveryState, TaskRecord


class TaskRegistryProcessState:
    """In-memory process state for task registry with indexed lookups."""

    def __init__(self) -> None:
        self.tasks: dict[str, TaskRecord] = {}
        self.task_delivery_states: dict[str, TaskDeliveryState] = {}
        self.task_ids_by_run_id: dict[str, set[str]] = {}
        self.task_ids_by_owner_key: dict[str, set[str]] = {}
        self.task_ids_by_parent_flow_id: dict[str, set[str]] = {}
        self.task_ids_by_related_session_key: dict[str, set[str]] = {}
        self.tasks_with_pending_delivery: set[str] = set()


_PROCESS_STATE: TaskRegistryProcessState | None = None


def get_task_registry_process_state() -> TaskRegistryProcessState:
    """Get the singleton process state, creating it if needed."""
    global _PROCESS_STATE
    if _PROCESS_STATE is None:
        _PROCESS_STATE = TaskRegistryProcessState()
    return _PROCESS_STATE


def reset_task_registry_process_state() -> None:
    """Reset the singleton process state (for testing)."""
    global _PROCESS_STATE
    _PROCESS_STATE = None
