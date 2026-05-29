"""Task and flow management system — types and pure logic.

Ported from OpenClaw src/tasks/

Contains core type definitions, completion contract analysis, summary
aggregation, retention policies, audit types, and detached task lifecycle contracts.
All files here are framework-agnostic with no OpenClaw-internal dependencies.
"""

from .types import (
    TaskRecord,
    TaskStatus,
    TaskRuntime,
    TaskDeliveryStatus,
    TaskNotifyPolicy,
    TaskTerminalOutcome,
    TaskScopeKind,
    TaskEventKind,
    TaskRegistrySummary,
    TaskStatusCounts,
    TaskRuntimeCounts,
    TaskDeliveryState,
    TaskEventRecord,
    TaskRegistrySnapshot,
    DeliveryContext,
)
from .flow_types import (
    TaskFlowRecord,
    TaskFlowStatus,
    TaskFlowSyncMode,
)
from .completion_contract import (
    RequiredCompletionTerminalResult,
    is_progress_only_completion_text,
    resolve_required_completion_terminal_result,
    resolve_required_completion_delivery_failure_terminal_result,
)
from .summary import (
    create_empty_task_registry_summary,
    summarize_task_records,
)
from .retention import (
    DEFAULT_TASK_RETENTION_MS,
    LOST_TASK_RETENTION_MS,
    resolve_task_retention_ms,
    resolve_task_cleanup_after,
    resolve_effective_task_cleanup_after,
)
from .process_state import (
    TaskRegistryProcessState,
    get_task_registry_process_state,
    reset_task_registry_process_state,
)
from .detached_contract import (
    DetachedTaskCreateParams,
    DetachedRunningTaskCreateParams,
    DetachedTaskStartParams,
    DetachedTaskProgressParams,
    DetachedTaskCompleteParams,
    DetachedTaskFailParams,
    DetachedTaskFinalizeParams,
    DetachedTaskDeliveryStatusParams,
    DetachedTaskCancelParams,
    DetachedTaskCancelResult,
    DetachedTaskRecoveryAttemptParams,
    DetachedTaskRecoveryAttemptResult,
    DetachedTaskLifecycleRuntime,
    DetachedTaskLifecycleRuntimeRegistration,
)
from .detached_state import (
    register_detached_task_lifecycle_runtime,
    get_detached_task_lifecycle_runtime_registration,
    get_registered_detached_task_lifecycle_runtime,
    clear_detached_task_lifecycle_runtime_registration,
)
from .codex_subagent import (
    CODEX_NATIVE_SUBAGENT_RUNTIME,
    CODEX_NATIVE_SUBAGENT_TASK_KIND,
    CODEX_NATIVE_SUBAGENT_RUN_ID_PREFIX,
    CODEX_NATIVE_SUBAGENT_STALE_ERROR,
    is_childless_codex_native_subagent_task,
)
from .audit import (
    TaskAuditSeverity,
    TaskAuditCode,
    TaskAuditFinding,
    TaskAuditSummary,
    create_empty_task_audit_summary,
    compare_task_audit_finding_sort_keys,
)
from .store_types import TaskRegistryStoreSnapshot

__all__ = [
    # Types
    "TaskRecord",
    "TaskStatus",
    "TaskRuntime",
    "TaskDeliveryStatus",
    "TaskNotifyPolicy",
    "TaskTerminalOutcome",
    "TaskScopeKind",
    "TaskEventKind",
    "TaskRegistrySummary",
    "TaskStatusCounts",
    "TaskRuntimeCounts",
    "TaskDeliveryState",
    "TaskEventRecord",
    "TaskRegistrySnapshot",
    "DeliveryContext",
    # Flow types
    "TaskFlowRecord",
    "TaskFlowStatus",
    "TaskFlowSyncMode",
    # Completion contract
    "RequiredCompletionTerminalResult",
    "is_progress_only_completion_text",
    "resolve_required_completion_terminal_result",
    "resolve_required_completion_delivery_failure_terminal_result",
    # Summary
    "create_empty_task_registry_summary",
    "summarize_task_records",
    # Retention
    "DEFAULT_TASK_RETENTION_MS",
    "LOST_TASK_RETENTION_MS",
    "resolve_task_retention_ms",
    "resolve_task_cleanup_after",
    "resolve_effective_task_cleanup_after",
    # Process state
    "TaskRegistryProcessState",
    "get_task_registry_process_state",
    "reset_task_registry_process_state",
    # Detached contract
    "DetachedTaskCreateParams",
    "DetachedRunningTaskCreateParams",
    "DetachedTaskStartParams",
    "DetachedTaskProgressParams",
    "DetachedTaskCompleteParams",
    "DetachedTaskFailParams",
    "DetachedTaskFinalizeParams",
    "DetachedTaskDeliveryStatusParams",
    "DetachedTaskCancelParams",
    "DetachedTaskCancelResult",
    "DetachedTaskRecoveryAttemptParams",
    "DetachedTaskRecoveryAttemptResult",
    "DetachedTaskLifecycleRuntime",
    "DetachedTaskLifecycleRuntimeRegistration",
    # Detached state
    "register_detached_task_lifecycle_runtime",
    "get_detached_task_lifecycle_runtime_registration",
    "get_registered_detached_task_lifecycle_runtime",
    "clear_detached_task_lifecycle_runtime_registration",
    # Codex subagent
    "CODEX_NATIVE_SUBAGENT_RUNTIME",
    "CODEX_NATIVE_SUBAGENT_TASK_KIND",
    "CODEX_NATIVE_SUBAGENT_RUN_ID_PREFIX",
    "CODEX_NATIVE_SUBAGENT_STALE_ERROR",
    "is_childless_codex_native_subagent_task",
    # Audit
    "TaskAuditSeverity",
    "TaskAuditCode",
    "TaskAuditFinding",
    "TaskAuditSummary",
    "create_empty_task_audit_summary",
    "compare_task_audit_finding_sort_keys",
    # Store types
    "TaskRegistryStoreSnapshot",
]
