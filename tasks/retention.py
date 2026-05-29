"""Task retention policy.

Ported from OpenClaw src/tasks/task-retention.ts
"""

from __future__ import annotations

from .types import TaskRecord, TaskStatus

DEFAULT_TASK_RETENTION_MS = 7 * 24 * 60 * 60_000  # 7 days
LOST_TASK_RETENTION_MS = 24 * 60 * 60_000  # 1 day


def resolve_task_retention_ms(status: str) -> int:
    """Get the retention period for a task based on its status."""
    return LOST_TASK_RETENTION_MS if status == TaskStatus.LOST else DEFAULT_TASK_RETENTION_MS


def resolve_task_cleanup_after(task: TaskRecord) -> int:
    """Calculate the cleanup-after timestamp for a task."""
    terminal_at = task.ended_at or task.last_event_at or task.created_at
    return terminal_at + resolve_task_retention_ms(task.status)


def resolve_effective_task_cleanup_after(task: TaskRecord) -> int:
    """Resolve the effective cleanup-after, respecting explicit overrides for non-lost tasks."""
    status_cleanup_after = resolve_task_cleanup_after(task)
    if task.cleanup_after is None:
        return status_cleanup_after
    if task.status == TaskStatus.LOST:
        return min(task.cleanup_after, status_cleanup_after)
    return task.cleanup_after
