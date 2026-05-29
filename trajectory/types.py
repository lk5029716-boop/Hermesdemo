"""Trajectory event types and bundle manifest structures.

Ported from OpenClaw src/trajectory/types.ts
Defines the core data structures for agent trajectory/audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrajectoryToolDefinition:
    """A tool definition captured in a trajectory trace."""

    name: str
    description: str | None = None
    parameters: Any = None


@dataclass
class TrajectoryEvent:
    """A single trajectory event in the agent audit trace.

    Each event records something that happened during an agent session:
    tool calls, messages, model responses, prompt submissions, etc.
    """

    trace_id: str
    source: str  # "runtime" | "transcript" | "export"
    type: str
    ts: str  # ISO 8601 timestamp
    seq: int
    session_id: str
    schema_version: int = 1
    source_seq: int | None = None
    session_key: str | None = None
    run_id: str | None = None
    workspace_dir: str | None = None
    provider: str | None = None
    model_id: str | None = None
    model_api: str | None = None
    entry_id: str | None = None
    parent_entry_id: str | None = None
    data: dict[str, Any] | None = None


@dataclass
class TrajectoryBundleWarning:
    """A warning generated during trajectory bundle export."""

    source: str  # "session" | "runtime"
    code: str
    count: int
    rows: list[int] = field(default_factory=list)
    message: str = ""


@dataclass
class TrajectoryBundleManifest:
    """Manifest for an exported trajectory bundle.

    A trajectory bundle is a directory containing:
    - manifest.json  → this structure
    - events.jsonl   → all trajectory events
    - session-branch.json → the session's message tree
    - (optional) system-prompt.txt, tools.json, metadata.json, etc.
    """

    trace_id: str
    session_id: str
    generated_at: str  # ISO 8601
    workspace_dir: str
    event_count: int
    runtime_event_count: int
    transcript_event_count: int
    source_files: dict[str, str | None]
    schema_version: int = 1
    session_key: str | None = None
    leaf_id: str | None = None
    contents: list[dict[str, Any]] | None = None
    supplemental_files: list[str] | None = None
    warnings: list[TrajectoryBundleWarning] | None = None
