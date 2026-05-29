"""
transcript_tools.py — Tool call extraction from messages.

Adapted from OpenClaw src/utils/transcript-tools.ts.

Extracts tool calls and tool results from agent message transcripts.
Useful for debugging, trajectory logging, and transcript analysis.

Hermes stores messages in OpenAI format; this provides utilities
for working with that format.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """A single tool call from a message."""
    id: str
    name: str
    arguments: str

    @property
    def args_dict(self) -> dict | None:
        try:
            return json.loads(self.arguments)
        except (json.JSONDecodeError, TypeError):
            return None


@dataclass
class ToolResult:
    """A tool result message."""
    tool_call_id: str
    role: str
    content: str


def extract_tool_calls(message: dict[str, Any]) -> list[ToolCall]:
    """Extract all tool calls from an assistant message."""
    tool_calls = message.get("tool_calls", [])
    if not tool_calls:
        return []

    results = []
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function", {})
        results.append(ToolCall(
            id=tc.get("id", ""),
            name=fn.get("name", ""),
            arguments=fn.get("arguments", ""),
        ))
    return results


def extract_tool_results(messages: list[dict[str, Any]]) -> list[ToolResult]:
    """Extract all tool result messages from a transcript."""
    results = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "")
        if role == "tool":
            results.append(ToolResult(
                tool_call_id=msg.get("tool_call_id", ""),
                role=role,
                content=str(msg.get("content", "")),
            ))
    return results


def has_tool_calls(message: dict[str, Any]) -> bool:
    """Check if a message contains tool calls."""
    tool_calls = message.get("tool_calls", [])
    return bool(tool_calls) and isinstance(tool_calls, list) and len(tool_calls) > 0


def is_tool_result(message: dict[str, Any]) -> bool:
    """Check if a message is a tool result."""
    return message.get("role") == "tool"


def extract_assistant_text(message: dict[str, Any]) -> str:
    """Extract text content from an assistant message (ignoring tool calls)."""
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return " ".join(parts)
    return str(content)
