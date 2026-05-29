"""Detached task lifecycle runtime contract types.

Ported from OpenClaw src/tasks/detached-task-runtime-contract.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import (
    DeliveryContext,
    TaskDeliveryStatus,
    TaskNotifyPolicy,
    TaskRecord,
    TaskRuntime,
    TaskScopeKind,
    TaskStatus,
    TaskTerminalOutcome,
)


@dataclass
class DetachedTaskCreateParams:
    runtime: TaskRuntime
    task: str
    task_kind: str | None = None
    source_id: str | None = None
    requester_session_key: str | None = None
    owner_key: str | None = None
    scope_kind: TaskScopeKind | None = None
    requester_origin: DeliveryContext | None = None
    parent_flow_id: str | None = None
    child_session_key: str | None = None
    parent_task_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None
    label: str | None = None
    prefer_metadata: bool = False
    notify_policy: TaskNotifyPolicy | None = None
    delivery_status: TaskDeliveryStatus | None = None


@dataclass
class DetachedRunningTaskCreateParams(DetachedTaskCreateParams):
    started_at: int | None = None
    last_event_at: int | None = None
    progress_summary: str | None = None


@dataclass
class DetachedTaskStartParams:
    run_id: str
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    started_at: int | None = None
    last_event_at: int | None = None
    progress_summary: str | None = None
    event_summary: str | None = None


@dataclass
class DetachedTaskProgressParams:
    run_id: str
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    last_event_at: int | None = None
    progress_summary: str | None = None
    event_summary: str | None = None


@dataclass
class DetachedTaskCompleteParams:
    run_id: str
    ended_at: int
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    last_event_at: int | None = None
    progress_summary: str | None = None
    terminal_summary: str | None = None
    terminal_outcome: TaskTerminalOutcome | None = None


@dataclass
class DetachedTaskFailParams:
    run_id: str
    ended_at: int
    status: str = TaskStatus.FAILED  # "failed" | "timed_out" | "cancelled"
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    last_event_at: int | None = None
    error: str | None = None
    progress_summary: str | None = None
    terminal_summary: str | None = None


@dataclass
class DetachedTaskFinalizeParams:
    run_id: str
    status: str  # "succeeded" | "failed" | "timed_out" | "cancelled"
    ended_at: int
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    last_event_at: int | None = None
    error: str | None = None
    progress_summary: str | None = None
    terminal_summary: str | None = None
    terminal_outcome: TaskTerminalOutcome | None = None


@dataclass
class DetachedTaskDeliveryStatusParams:
    run_id: str
    delivery_status: TaskDeliveryStatus
    runtime: TaskRuntime | None = None
    session_key: str | None = None
    error: str | None = None


@dataclass
class DetachedTaskCancelParams:
    task_id: str
    reason: str | None = None


@dataclass
class DetachedTaskCancelResult:
    found: bool = False
    cancelled: bool = False
    reason: str | None = None
    task: TaskRecord | None = None


@dataclass
class DetachedTaskRecoveryAttemptParams:
    task_id: str
    runtime: TaskRuntime
    task: TaskRecord
    now: int


@dataclass
class DetachedTaskRecoveryAttemptResult:
    recovered: bool = False


@dataclass
class DetachedTaskLifecycleRuntime:
    """Interface for detached task lifecycle management.

    Implementations handle creating, starting, progressing, completing,
    failing, and canceling detached task runs.
    """
    create_queued_task_run: Any = None
    create_running_task_run: Any = None
    start_task_run_by_run_id: Any = None
    record_task_run_progress_by_run_id: Any = None
    finalize_task_run_by_run_id: Any = None
    complete_task_run_by_run_id: Any = None
    fail_task_run_by_run_id: Any = None
    set_detached_task_delivery_status_by_run_id: Any = None
    cancel_detached_task_run_by_id: Any = None
    try_recover_task_before_mark_lost: Any = None


@dataclass
class DetachedTaskLifecycleRuntimeRegistration:
    plugin_id: str
    runtime: DetachedTaskLifecycleRuntime
