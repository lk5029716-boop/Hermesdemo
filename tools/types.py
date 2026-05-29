"""Tool management type definitions.

Ported from OpenClaw src/tools/types.ts
Defines core types for tool descriptors, availability expressions, and tool plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# --- JSON type aliases ---
# In Python, JsonValue is effectively Any, but we keep the structure documented.

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class ToolOwnerKind(str, Enum):
    CORE = "core"
    PLUGIN = "plugin"
    CHANNEL = "channel"
    MCP = "mcp"


class ToolExecutorKind(str, Enum):
    CORE = "core"
    PLUGIN = "plugin"
    CHANNEL = "channel"
    MCP = "mcp"


class ToolUnavailableReason(str, Enum):
    AUTH_MISSING = "auth-missing"
    CONFIG_MISSING = "config-missing"
    CONTEXT_MISMATCH = "context-mismatch"
    ENV_MISSING = "env-missing"
    PLUGIN_DISABLED = "plugin-disabled"
    UNSUPPORTED_SIGNAL = "unsupported-signal"


class ToolAvailabilitySignalKind(str, Enum):
    ALWAYS = "always"
    AUTH = "auth"
    CONFIG = "config"
    ENV = "env"
    PLUGIN_ENABLED = "plugin-enabled"
    CONTEXT = "context"


@dataclass
class ToolOwnerRef:
    kind: ToolOwnerKind
    plugin_id: str | None = None
    channel_id: str | None = None
    server_id: str | None = None


@dataclass
class ToolExecutorRef:
    kind: ToolExecutorKind
    executor_id: str | None = None
    plugin_id: str | None = None
    tool_name: str | None = None
    channel_id: str | None = None
    action_id: str | None = None
    server_id: str | None = None


@dataclass
class ToolAvailabilitySignal:
    kind: ToolAvailabilitySignalKind
    provider_id: str | None = None
    path: list[str] = field(default_factory=list)
    check: str | None = None  # "exists" | "non-empty" | "available"
    name: str | None = None  # for env kind
    plugin_id: str | None = None  # for plugin-enabled kind
    key: str | None = None  # for context kind
    equals: JsonPrimitive | None = None  # for context kind


@dataclass
class ToolAvailabilityExpression:
    """A composable availability expression.

    Can be a single signal, an allOf (AND), or an anyOf (OR) group.
    """
    signal: ToolAvailabilitySignal | None = None
    all_of: list[ToolAvailabilityExpression] | None = None
    any_of: list[ToolAvailabilityExpression] | None = None


@dataclass
class ToolDescriptor:
    """Describes a tool available to the agent."""
    name: str
    description: str
    input_schema: JsonObject
    owner: ToolExecutorRef
    title: str | None = None
    output_schema: JsonObject | None = None
    executor: ToolExecutorRef | None = None
    availability: ToolAvailabilityExpression | None = None
    annotations: JsonObject | None = None
    sort_key: str | None = None


@dataclass
class ToolAvailabilityContext:
    """Context used to evaluate tool availability."""
    auth_provider_ids: set[str] | None = None
    config: JsonObject | None = None
    env: dict[str, str | None] | None = None
    enabled_plugin_ids: set[str] | None = None
    values: dict[str, JsonPrimitive | None] | None = None
    is_config_value_available: callable | None = None


@dataclass
class ToolAvailabilityDiagnostic:
    """Explains why a tool is unavailable."""
    reason: ToolUnavailableReason
    signal: ToolAvailabilitySignal | None = None
    message: str = ""


@dataclass
class ToolPlanEntry:
    descriptor: ToolDescriptor
    executor: ToolExecutorRef


@dataclass
class HiddenToolPlanEntry:
    descriptor: ToolDescriptor
    diagnostics: list[ToolAvailabilityDiagnostic] = field(default_factory=list)


@dataclass
class ToolPlan:
    """Result of building a tool plan — visible and hidden tools."""
    visible: list[ToolPlanEntry] = field(default_factory=list)
    hidden: list[HiddenToolPlanEntry] = field(default_factory=list)


@dataclass
class ToolProtocolDescriptor:
    """Minimal tool descriptor for protocol/API exposure."""
    name: str
    description: str
    input_schema: JsonObject


@dataclass
class BuildToolPlanOptions:
    descriptors: list[ToolDescriptor]
    availability: ToolAvailabilityContext | None = None
