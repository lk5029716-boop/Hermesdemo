"""Tool protocol descriptor conversion.

Ported from OpenClaw src/tools/protocol.ts
"""

from __future__ import annotations

from .types import JsonObject, ToolPlanEntry, ToolProtocolDescriptor


def to_tool_protocol_descriptor(entry: ToolPlanEntry) -> ToolProtocolDescriptor:
    """Convert a ToolPlanEntry to a minimal protocol descriptor.

    Shared descriptor shape only. Model/provider adapters still own schema normalization.
    """
    return ToolProtocolDescriptor(
        name=entry.descriptor.name,
        description=entry.descriptor.description,
        input_schema=entry.descriptor.input_schema,
    )


def to_tool_protocol_descriptors(
    entries: list[ToolPlanEntry],
) -> list[ToolProtocolDescriptor]:
    """Convert multiple ToolPlanEntries to protocol descriptors."""
    return [to_tool_protocol_descriptor(entry) for entry in entries]
