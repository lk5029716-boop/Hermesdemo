"""Trajectory system — agent audit trace capture and export.

Ported from OpenClaw src/trajectory/

Provides data structures and path utilities for recording a detailed
trace of everything an agent does during a session (tool calls, messages,
model responses, prompts) and exporting it as a diagnostic bundle.

Modules:
    types  — Core data classes (TrajectoryEvent, TrajectoryBundleManifest, etc.)
    paths  — File path resolution and safety utilities
"""

from .paths import (
    TRAJECTORY_RUNTIME_CAPTURE_MAX_BYTES,
    TRAJECTORY_RUNTIME_EVENT_MAX_BYTES,
    TRAJECTORY_RUNTIME_FILE_MAX_BYTES,
    resolve_trajectory_file_path,
    resolve_trajectory_pointer_file_path,
    safe_trajectory_session_file_name,
)
from .types import (
    TrajectoryBundleManifest,
    TrajectoryBundleWarning,
    TrajectoryEvent,
    TrajectoryToolDefinition,
)

__all__ = [
    "TrajectoryBundleManifest",
    "TrajectoryBundleWarning",
    "TrajectoryEvent",
    "TrajectoryToolDefinition",
    "TRAJECTORY_RUNTIME_CAPTURE_MAX_BYTES",
    "TRAJECTORY_RUNTIME_EVENT_MAX_BYTES",
    "TRAJECTORY_RUNTIME_FILE_MAX_BYTES",
    "resolve_trajectory_file_path",
    "resolve_trajectory_pointer_file_path",
    "safe_trajectory_session_file_name",
]
