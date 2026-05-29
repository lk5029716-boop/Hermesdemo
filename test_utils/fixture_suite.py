"""Test fixture suite — temp dir-based test case management.

Ported from OpenClaw src/test-utils/fixture-suite.ts
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field


@dataclass
class FixtureSuite:
    """Creates a temp root directory and numbered case subdirectories.

    Usage:
        suite = create_fixture_suite("my-test-")
        await suite.setup()
        case_dir = await suite.create_case_dir("scenario")
        # ... test code ...
        await suite.cleanup()
    """

    root_prefix: str
    _fixture_root: str = ""
    _fixture_count: int = 0

    async def setup(self) -> None:
        self._fixture_root = tempfile.mkdtemp(prefix=self.root_prefix)

    async def cleanup(self) -> None:
        if self._fixture_root:
            import shutil
            shutil.rmtree(self._fixture_root, ignore_errors=True)
            self._fixture_root = ""

    async def create_case_dir(self, prefix: str) -> str:
        if not self._fixture_root:
            raise RuntimeError("Fixture suite not initialized — call setup() first")
        dir_path = os.path.join(self._fixture_root, f"{prefix}-{self._fixture_count}")
        self._fixture_count += 1
        os.makedirs(dir_path, exist_ok=True)
        return dir_path


def create_fixture_suite(root_prefix: str) -> FixtureSuite:
    """Create a new fixture suite."""
    return FixtureSuite(root_prefix=root_prefix)
