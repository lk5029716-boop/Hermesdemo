"""Codex native subagent task detection.

Ported from OpenClaw src/tasks/codex-native-subagent-task.ts
"""

from __future__ import annotations

from .types import TaskRecord, TaskRuntime

CODEX_NATIVE_SUBAGENT_RUNTIME = TaskRuntime.SUBAGENT
CODEX_NATIVE_SUBAGENT_TASK_KIND = "codex-native"
CODEX_NATIVE_SUBAGENT_RUN_ID_PREFIX = "codex-thread:"
CODEX_NATIVE_SUBAGENT_STALE_ERROR = "Codex native subagent stopped reporting progress"


def is_childless_codex_native_subagent_task(task: TaskRecord) -> bool:
    """Check if a task is a childless Codex native subagent task.

    These are subagent tasks that were created by the Codex harness
    directly without spawning a child session.
    """
    if task.runtime != CODEX_NATIVE_SUBAGENT_RUNTIME:
        return False
    if task.task_kind != CODEX_NATIVE_SUBAGENT_TASK_KIND:
        return False
    if task.child_session_key and task.child_session_key.strip():
        return False
    return any(
        candidate and candidate.strip().startswith(CODEX_NATIVE_SUBAGENT_RUN_ID_PREFIX)
        for candidate in (task.source_id, task.run_id)
    )
