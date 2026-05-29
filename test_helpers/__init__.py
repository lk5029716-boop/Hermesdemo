"""Test helper utilities.

Ported from OpenClaw src/test-helpers/

Advanced test helpers for temp dirs, workspaces, HTTP fixtures, and Windows shims.
This is distinct from test_utils/ which contains more generic utilities.
"""

from .http import json_response, request_body_text, request_url
from .temp_dir import (
    SuiteTempRootTracker,
    create_suite_temp_root_tracker,
    with_temp_dir,
    with_temp_dir_sync,
)
from .windows_cmd_shim import create_windows_cmd_shim_fixture
from .workspace import make_temp_workspace, write_workspace_file

__all__ = [
    "SuiteTempRootTracker",
    "create_suite_temp_root_tracker",
    "create_windows_cmd_shim_fixture",
    "json_response",
    "make_temp_workspace",
    "request_body_text",
    "request_url",
    "with_temp_dir",
    "with_temp_dir_sync",
    "write_workspace_file",
]
