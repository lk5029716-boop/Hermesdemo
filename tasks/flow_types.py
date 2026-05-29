"""Task flow registry type definitions.

Ported from OpenClaw src/tasks/task-flow-registry.types.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .types import DeliveryContext, TaskNotifyPolicy


class TaskFlowSyncMode(str, Enum):
    TASK_MIRRORED = "task_mirrored"
    MANAGED = "managed"


class TaskFlowStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LOST = "lost"


@dataclass
class TaskFlowRecord:
    flow_id: str
    sync_mode: TaskFlowSyncMode
    owner_key: str
    status: TaskFlowStatus
    notify_policy: TaskNotifyPolicy
    goal: str
    revision: int = 0
    requester_origin: DeliveryContext | None = None
    controller_id: str | None = None
    current_step: str | None = None
    blocked_task_id: str | None = None
    blocked_summary: str | None = None
    state_json: Any = None
    wait_json: Any = None
    cancel_requested_at: int | None = None
    created_at: int = 0
    updated_at: int = 0
    ended_at: int | None = None
