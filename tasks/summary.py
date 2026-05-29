"""Task registry summary aggregation.

Ported from OpenClaw src/tasks/task-registry.summary.ts
"""

from __future__ import annotations

from .types import (
    TaskRecord,
    TaskRegistrySummary,
    TaskRuntimeCounts,
    TaskStatusCounts,
    TaskStatus,
    TaskRuntime,
)


def create_empty_status_counts() -> TaskStatusCounts:
    return TaskStatusCounts()


def create_empty_runtime_counts() -> TaskRuntimeCounts:
    return TaskRuntimeCounts()


def create_empty_task_registry_summary() -> TaskRegistrySummary:
    return TaskRegistrySummary(
        by_status=create_empty_status_counts(),
        by_runtime=create_empty_runtime_counts(),
    )


def summarize_task_records(records: list[TaskRecord]) -> TaskRegistrySummary:
    """Aggregate task records into a summary with counts by status and runtime."""
    summary = create_empty_task_registry_summary()
    for task in records:
        summary.total += 1
        summary.by_status.__dict__[task.status.value] += 1
        summary.by_runtime.__dict__[task.runtime.value] += 1
        if task.status in (TaskStatus.QUEUED, TaskStatus.RUNNING):
            summary.active += 1
        else:
            summary.terminal += 1
        if task.status in (TaskStatus.FAILED, TaskStatus.TIMED_OUT, TaskStatus.LOST):
            summary.failures += 1
    return summary
