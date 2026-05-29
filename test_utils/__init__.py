"""Test utilities — generic helpers for Python tests.

Ported from OpenClaw src/test-utils/

Contains only the portable, framework-agnostic utilities.
Vitest-specific helpers are not included.
"""

from .chunk_test_helpers import count_lines, has_balanced_fences
from .env import (
    capture_env,
    capture_full_env,
    create_path_resolution_env,
    with_env,
    with_env_async,
)
from .fixture_suite import FixtureSuite, create_fixture_suite
from .internal_hook_event_payload import create_internal_hook_event_payload
from .node_process import (
    exec_node_eval_sync,
    node_eval_json,
    spawn_node_eval_sync,
)
from .ports import get_deterministic_free_port_block
from .repo_files import list_git_tracked_files, sort_repo_paths, to_repo_path
from .secret_file_fixture import with_temp_secret_files
from .secret_ref_test_vectors import (
    INVALID_EXEC_SECRET_REF_IDS,
    INVALID_FILE_SECRET_REF_IDS,
    VALID_EXEC_SECRET_REF_IDS,
    VALID_FILE_SECRET_REF_IDS,
)
from .temp_dir import with_temp_dir

__all__ = [
    "FixtureSuite",
    "capture_env",
    "capture_full_env",
    "count_lines",
    "create_fixture_suite",
    "create_internal_hook_event_payload",
    "create_path_resolution_env",
    "exec_node_eval_sync",
    "get_deterministic_free_port_block",
    "has_balanced_fences",
    "INVALID_EXEC_SECRET_REF_IDS",
    "INVALID_FILE_SECRET_REF_IDS",
    "list_git_tracked_files",
    "node_eval_json",
    "sort_repo_paths",
    "spawn_node_eval_sync",
    "to_repo_path",
    "VALID_EXEC_SECRET_REF_IDS",
    "VALID_FILE_SECRET_REF_IDS",
    "with_env",
    "with_env_async",
    "with_temp_dir",
    "with_temp_secret_files",
]
