"""Tool executor reference formatting.

Ported from OpenClaw src/tools/execution.ts
"""

from __future__ import annotations

from .types import ToolExecutorKind, ToolExecutorRef


def format_tool_executor_ref(ref: ToolExecutorRef) -> str:
    """Format a ToolExecutorRef as a human-readable string.

    Examples:
        core:shell
        plugin:weather:get_forecast
        channel:telegram:send_message
        mcp:filesystem:read_file
    """
    match ref.kind:
        case ToolExecutorKind.CORE:
            return f"core:{ref.executor_id}"
        case ToolExecutorKind.PLUGIN:
            return f"plugin:{ref.plugin_id}:{ref.tool_name}"
        case ToolExecutorKind.CHANNEL:
            return f"channel:{ref.channel_id}:{ref.action_id}"
        case ToolExecutorKind.MCP:
            return f"mcp:{ref.server_id}:{ref.tool_name}"
        case _:
            raise ValueError(f"Unknown executor kind: {ref.kind}")
