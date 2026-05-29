"""Tool management system — descriptors, availability, and planning.

Ported from OpenClaw src/tools/

Provides:
    - Type definitions for tool descriptors, availability expressions, and tool plans
    - Tool availability evaluation (auth, config, env, plugin, context-based)
    - Tool plan builder (sorts, deduplicates, evaluates, separates visible/hidden)
    - Protocol descriptor conversion
    - Executor reference formatting
"""

from .availability import evaluate_tool_availability
from .descriptors import define_tool_descriptor, define_tool_descriptors
from .diagnostics import ToolPlanContractError
from .execution import format_tool_executor_ref
from .planner import build_tool_plan
from .protocol import to_tool_protocol_descriptor, to_tool_protocol_descriptors
from .types import (
    BuildToolPlanOptions,
    HiddenToolPlanEntry,
    ToolAvailabilityContext,
    ToolAvailabilityDiagnostic,
    ToolAvailabilityExpression,
    ToolAvailabilitySignal,
    ToolAvailabilitySignalKind,
    ToolDescriptor,
    ToolExecutorKind,
    ToolExecutorRef,
    ToolOwnerKind,
    ToolOwnerRef,
    ToolPlan,
    ToolPlanEntry,
    ToolProtocolDescriptor,
    ToolUnavailableReason,
)

__all__ = [
    "ToolPlanContractError",
    "ToolProtocolDescriptor",
    "BuildToolPlanOptions",
    "HiddenToolPlanEntry",
    "ToolAvailabilityContext",
    "ToolAvailabilityDiagnostic",
    "ToolAvailabilityExpression",
    "ToolAvailabilitySignal",
    "ToolAvailabilitySignalKind",
    "ToolDescriptor",
    "ToolExecutorKind",
    "ToolExecutorRef",
    "ToolOwnerKind",
    "ToolOwnerRef",
    "ToolPlan",
    "ToolPlanEntry",
    "ToolUnavailableReason",
    "build_tool_plan",
    "define_tool_descriptor",
    "define_tool_descriptors",
    "evaluate_tool_availability",
    "format_tool_executor_ref",
    "to_tool_protocol_descriptor",
    "to_tool_protocol_descriptors",
]
