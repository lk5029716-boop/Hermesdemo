"""Tool plan contract error.

Ported from OpenClaw src/tools/diagnostics.ts
"""

from __future__ import annotations


class ToolPlanContractError(Exception):
    """Raised when a tool plan fails validation (duplicate name, missing executor)."""

    def __init__(self, code: str, tool_name: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.tool_name = tool_name
