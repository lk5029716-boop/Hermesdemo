"""Trajectory file path resolution and safety utilities.

Ported from OpenClaw src/trajectory/paths.ts
Resolves where trajectory JSONL files are stored and validates path safety.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# Size limits for trajectory capture
TRAJECTORY_RUNTIME_CAPTURE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
TRAJECTORY_RUNTIME_FILE_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
TRAJECTORY_RUNTIME_EVENT_MAX_BYTES = 256 * 1024  # 256 KB


def safe_trajectory_session_file_name(session_id: str) -> str:
    """Sanitize a session ID for use as a filename.

    Replaces non-alphanumeric characters with underscores and
    truncates to 120 characters. Falls back to "session" if
    the result has no alphanumeric characters.
    """
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:120]
    return safe if safe and any(c.isalnum() for c in safe) else "session"


def _is_path_inside(parent: Path, child: Path) -> bool:
    """Check that child is strictly inside parent (not equal to parent)."""
    try:
        child.relative_to(parent)
        return child != parent
    except ValueError:
        return False


def _resolve_contained_path(base_dir: Path, file_name: str) -> Path:
    """Resolve a file path and verify it stays within base_dir.

    Raises ValueError if the resolved path escapes the base directory.
    """
    resolved_base = base_dir.resolve()
    resolved_file = (resolved_base / file_name).resolve()
    if resolved_file == resolved_base or not _is_path_inside(resolved_base, resolved_file):
        raise ValueError("Trajectory file path escaped its configured directory")
    return resolved_file


def resolve_trajectory_file_path(
    session_id: str,
    session_file: str | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    """Resolve the trajectory runtime file path for a session.

    Resolution order:
    1. OPENCLAW_TRAJECTORY_DIR env var → <dir>/<session>.jsonl
    2. session_file provided → <session_file>.trajectory.jsonl
    3. Fallback → cwd/<session>.trajectory.jsonl
    """
    effective_env: dict[str, str] = env if env is not None else dict(os.environ)
    dir_override = (effective_env.get("OPENCLAW_TRAJECTORY_DIR") or "").strip()
    safe_name = safe_trajectory_session_file_name(session_id)

    if dir_override:
        base = Path(dir_override).expanduser().resolve()
        return _resolve_contained_path(base, f"{safe_name}.jsonl")

    if session_file:
        sf = Path(session_file)
        if sf.suffix == ".jsonl":
            return sf.with_suffix(".trajectory.jsonl")
        return Path(f"{session_file}.trajectory.jsonl")

    return Path.cwd() / f"{safe_name}.trajectory.jsonl"


def resolve_trajectory_pointer_file_path(session_file: str) -> Path:
    """Resolve the trajectory pointer file path for a session.

    The pointer file is a small JSON file that records where the
    trajectory runtime JSONL file lives, so it can be found later
    without re-deriving the path.
    """
    sf = Path(session_file)
    if sf.suffix == ".jsonl":
        return sf.with_suffix(".trajectory-path.json")
    return Path(f"{session_file}.trajectory-path.json")
