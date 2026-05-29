"""Git-tracked file listing utilities.

Ported from OpenClaw src/test-utils/repo-files.ts
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def to_repo_path(file_path: str) -> str:
    """Normalize a file path to forward-slash repo convention."""
    return file_path.replace("\\", "/")


def to_repo_relative_path(repo_root: str, file_path: str) -> str:
    """Convert an absolute path to a repo-relative forward-slash path."""
    return to_repo_path(str(Path(file_path).relative_to(repo_root)))


def sort_repo_paths(paths: list[str]) -> list[str]:
    """Normalize and sort repo paths."""
    return sorted(to_repo_path(p) for p in paths)


def list_git_tracked_files(
    pathspecs: str | list[str],
    repo_root: str | None = None,
) -> list[str] | None:
    """List git-tracked files matching the given pathspecs.

    Returns None if git command fails. Results are sorted and normalized.
    """
    if isinstance(pathspecs, str):
        pathspecs = [pathspecs]
    repo_root = repo_root or "."
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", *pathspecs],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=16,
        )
        if result.returncode != 0:
            return None
        files = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]
        return sort_repo_paths(files)
    except Exception:
        return None
