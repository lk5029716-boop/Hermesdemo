"""Safe regex patterns and path scanning utilities.

Ported from OpenClaw src/security/safe-regex.ts and scan-paths.ts
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class SafeRegexReplacer:
    """Detects and replaces unsafe regex patterns with safe alternatives."""

    def __init__(self, sev_max: str = "limited") -> None:
        if sev_max == "off":
            self._sev = 0
        elif sev_max == "limited":
            self._sev = 1
        elif sev_max == "pedantic":
            self._sev = 2
        else:
            self._sev = 1

    def _ensure_safe_pattern(self, pattern: str) -> tuple[bool, str]:
        """Check if a regex pattern is safe (no catastrophic backtracking)."""
        # Simplified: flag obviously dangerous patterns
        if self._sev >= 1:
            # Detect nested quantifiers like (a+)+ or (a*)*
            if re.search(r"\([^\)]*[+*]\)[+*]", pattern):
                return False, pattern
            # Detect overlapping alternations with quantifiers
            if re.search(r"\([^\|]+\|[^\)]+\)[+*].*\1", pattern):
                return False, pattern
        return True, pattern

    def make_safe(
        self, patterns: list[str], replacement: str = "[REDACTED]"
    ) -> list[tuple[str, str]]:
        """Process patterns and replace unsafe ones."""
        results: list[tuple[str, str]] = []
        for pat in patterns:
            safe, cleaned = self._ensure_safe_pattern(pat)
            results.append((replacement if not safe else cleaned, pat))
        return results


def is_safe_pattern(pattern: str) -> bool:
    """Quick check if a regex pattern is safe from catastrophic backtracking."""
    try:
        re.compile(pattern)
    except re.error:
        return False
    # Flag nested quantifiers (e.g., (a+)+)
    if re.search(r"\([^)]*[+*]\)[+*]", pattern):
        return False
    # Flag exponential backtracking patterns
    if re.search(r"(?:.*){4,}", pattern):
        return False
    if re.search(r"\.\*[+?]\.\*[+?]", pattern):
        return False
    return True


# --- Path scanning ---


def is_path_inside(parent: str, child: str) -> bool:
    """Check that child is strictly inside parent (not equal to parent)."""
    try:
        child_path = Path(child).resolve()
        parent_path = Path(parent).resolve()
        child_path.relative_to(parent_path)
        return child_path != parent_path
    except (ValueError, RuntimeError):
        return False


def is_path_within_any(parent_dirs: list[str], target: str) -> bool:
    """Check if target path is inside any of the parent directories."""
    return any(is_path_inside(p, target) for p in parent_dirs)


def has_path_traversal(path: str) -> bool:
    """Check if a path contains traversal components (..)."""
    normalized = os.path.normpath(path)
    parts = normalized.replace("\\", "/").split("/")
    return ".." in parts


def safe_resolve_path(base_dir: str, user_path: str) -> str | None:
    """Safely resolve a user-provided path within a base directory.

    Returns None if the resolved path escapes the base directory.
    """
    if has_path_traversal(user_path):
        return None
    try:
        base = Path(base_dir).resolve()
        target = (base / user_path).resolve()
        target.relative_to(base)  # Raises ValueError if outside
        return str(target)
    except (ValueError, RuntimeError):
        return None
