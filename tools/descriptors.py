"""Tool descriptor helpers.

Ported from OpenClaw src/tools/descriptors.ts
"""

from __future__ import annotations

from .types import ToolDescriptor


def define_tool_descriptor(descriptor: ToolDescriptor) -> ToolDescriptor:
    """Identity helper for defining a tool descriptor (validates shape at type level)."""
    return descriptor


def define_tool_descriptors(
    descriptors: list[ToolDescriptor],
) -> list[ToolDescriptor]:
    """Identity helper for defining multiple tool descriptors."""
    return descriptors
