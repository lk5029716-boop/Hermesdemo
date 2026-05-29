"""Task registry core type definitions.

Ported from OpenClaw src/tasks/task-registry.types.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskRuntime(str, Enum):
    SUBAGENT = "subagent"
    ACP = "acp"
    CLI = "cli"
    CRON = "cron"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    LOST = "lost"


class TaskDeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    SESSION_QUEUED = "session_queued"
    FAILED = "failed"
    PARENT_MISSING = "parent_missing"
    NOT_APPLICABLE = "not_applicable"


class TaskNotifyPolicy(str, Enum):
    DONE_ONLY = "done_only"
    STATE_CHANGES = "state_changes"
    SILENT = "silent"


class TaskTerminalOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"


class TaskScopeKind(str, Enum):
    SESSION = "session"
    SYSTEM = "system"


class TaskEventKind(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    LOST = "lost"
    PROGRESS = "progress"


@dataclass
class DeliveryContext:
    """Context about where a task originated."""
    channel: str | None = None
    to: str | None = None
    thread_id: str | None = None
    sender_id: str | None = None
    account_id: str | None = None


@dataclass
class TaskStatusCounts:
    queued: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    timed_out: int = 0
    cancelled: int = 0
    lost: int = 0


@dataclass
class TaskRuntimeCounts:
    subagent: int = 0
    acp: int = 0
    cli: int = 0
    cron: int = 0


@dataclass
class TaskRegistrySummary:
    total: int = 0
    active: int = 0
    terminal: int = 0
    failures: int = 0
    by_status: TaskStatusCounts = field(default_factory=TaskStatusCounts)
    by_runtime: TaskRuntimeCounts = field(default_factory=TaskRuntimeCounts)


@dataclass
class TaskEventRecord:
    at: int
    kind: TaskEventKind
    summary: str | None = None


@dataclass
class TaskDeliveryState:
    task_id: str
    requester_origin: DeliveryContext | None = None
    last_notified_event_at: int | None = None


@dataclass
class TaskRecord:
    task_id: str
    runtime: TaskRuntime
    requester_session_key: str
    owner_key: str
    scope_kind: TaskScopeKind
    status: TaskStatus
    delivery_status: TaskDeliveryStatus
    notify_policy: TaskNotifyPolicy
    created_at: int
    task_kind: str | None = None
    source_id: str | None = None
    child_session_key: str | None = None
    parent_flow_id: str | None = None
    parent_task_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None
    label: str | None = None
    task: str = ""
    started_at: int | None = None
    ended_at: int | None = None
    last_event_at: int | None = None
    cleanup_after: int | None = None
    error: str | None = None
    progress_summary: str | None = None
    terminal_summary: str | None = None
    terminal_outcome: str | None = None


@dataclass
class TaskRegistrySnapshot:
    tasks: list[TaskRecord] = field(default_factory=list)
    delivery_states: list[TaskDeliveryState] = field(default_factory=list)
