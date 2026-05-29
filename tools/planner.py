"""Tool plan builder.

Ported from OpenClaw src/tools/planner.ts

Builds a tool plan from a list of descriptors:
- Sorts by sort_key/name
- Deduplicates by name (throws on duplicates)
- Evaluates availability — unavailable tools go to hidden list
- Visible tools must have an executor ref (throws if missing)
"""

from __future__ import annotations

from .availability import evaluate_tool_availability
from .diagnostics import ToolPlanContractError
from .types import (
    BuildToolPlanOptions,
    HiddenToolPlanEntry,
    ToolDescriptor,
    ToolPlan,
    ToolPlanEntry,
)


def _compare_descriptors(left: ToolDescriptor, right: ToolDescriptor) -> int:
    """Sort descriptors by sort_key (falls back to name)."""
    left_key = left.sort_key or left.name
    right_key = right.sort_key or right.name
    if left_key != right_key:
        return -1 if left_key < right_key else 1
    if left.name != right.name:
        return -1 if left.name < right.name else 1
    return 0


def _assert_unique_names(descriptors: list[ToolDescriptor]) -> None:
    """Throw ToolPlanContractError if any two descriptors share a name."""
    seen: set[str] = set()
    for descriptor in descriptors:
        if descriptor.name in seen:
            raise ToolPlanContractError(
                code="duplicate-tool-name",
                tool_name=descriptor.name,
                message=f"Duplicate tool descriptor name: {descriptor.name}",
            )
        seen.add(descriptor.name)


def build_tool_plan(
    descriptors: list[ToolDescriptor],
    availability_ctx=None,
) -> ToolPlan:
    """Build a ToolPlan from a list of descriptors.

    Steps:
    1. Sort descriptors by sort_key/name
    2. Assert unique names (raises ToolPlanContractError)
    3. Evaluate availability for each descriptor
       - Unavailable tools → hidden list with diagnostics
    4. Available tools must have an executor ref (raises ToolPlanContractError)
    """
    import functools

    sorted_descriptors = sorted(descriptors, key=functools.cmp_to_key(_compare_descriptors))
    _assert_unique_names(sorted_descriptors)

    visible: list[ToolPlanEntry] = []
    hidden: list[HiddenToolPlanEntry] = []

    for descriptor in sorted_descriptors:
        diagnostics = evaluate_tool_availability(
            descriptor, context=availability_ctx
        )
        if diagnostics:
            hidden.append(
                HiddenToolPlanEntry(descriptor=descriptor, diagnostics=diagnostics)
            )
            continue
        if descriptor.executor is None:
            raise ToolPlanContractError(
                code="missing-executor",
                tool_name=descriptor.name,
                message=f"Visible tool descriptor has no executor ref: {descriptor.name}",
            )
        visible.append(
            ToolPlanEntry(descriptor=descriptor, executor=descriptor.executor)
        )

    return ToolPlan(visible=visible, hidden=hidden)
