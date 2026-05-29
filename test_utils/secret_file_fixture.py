"""Temp secret file fixture helper.

Ported from OpenClaw src/test-utils/secret-file-fixture.ts
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, TypeVar

T = TypeVar("T")


class SecretFiles(TypedDict, total=False):
    password_file: str
    token_file: str


async def with_temp_secret_files(
    prefix: str,
    secrets: dict[str, str | None],
    run: Callable[[SecretFiles], T],
) -> T:
    """Create temporary files containing secret values, run a function, then clean up.

    Args:
        prefix: Temp directory prefix
        secrets: Dict with optional 'password' and 'token' keys
        run: Function receiving paths to the secret files
    """
    dir_path = tempfile.mkdtemp(prefix=prefix)
    files: SecretFiles = {}
    try:
        token_val = secrets.get("token")
        if token_val is not None:
            token_path = os.path.join(dir_path, "token.txt")
            Path(token_path).write_text(token_val)
            files["token_file"] = token_path
        password_val = secrets.get("password")
        if password_val is not None:
            password_path = os.path.join(dir_path, "password.txt")
            Path(password_path).write_text(password_val)
            files["password_file"] = password_path
        return run(files)
    finally:
        import shutil
        shutil.rmtree(dir_path, ignore_errors=True)
