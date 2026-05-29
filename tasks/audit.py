"""Task audit finding types and comparison.

Ported from OpenClaw src/tasks/task-registry.audit.shared.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .types import TaskRecord


class TaskAuditSeverity(str, Enum):
    WARN = "warn"
    ERROR = "error"


class TaskAuditCode(str, Enum):
    STALE_QUEUED = "stale_queued"
    STALE_RUNNING = "stale_running"
    LOST = "lost"
    DELIVERY_FAILED = "delivery_failed"
    MISSING_CLEANUP = "missing_cleanup"
    INCONSISTENT_TIMESTAMPS = "inconsistent_timestamps"


@dataclass
class TaskAuditFinding:
    severity: TaskAuditSeverity
    code: TaskAuditCode
    task: TaskRecord
    detail: str
    age_ms: int | None = None


@dataclass
class TaskAuditSummary:
    total: int = 0
    warnings: int = 0
    errors: int = 0
    by_code: dict[str, int] = field(default_factory=lambda: {
        code.value: 0 for code in TaskAuditCode
    })


def create_empty_task_audit_summary() -> TaskAuditSummary:
    return TaskAuditSummary()


def compare_task_audit_finding_sort_keys(
    left: TaskAuditFinding,
    right: TaskAuditFinding,
) -> int:
    """Sort key comparator: errors first, then by age (oldest first), then by creation time."""
    severity_rank = {"error": 0, "warn": 1}
    severity_diff = severity_rank.get(left.severity, 1) - severity_rank.get(right.severity, 1)
    if severity_diff != 0:
        return severity_diff
    left_age = left.age_ms if left.age_ms is not None else -1
    right_age = right.age_ms if right.age_ms is not None else -1
    if left_age != right_age:
        return right_age - left_age  # Older first
    return left.task.created_at - right.task.created_at
