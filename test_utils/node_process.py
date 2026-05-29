"""Node.js eval execution helpers.

Ported from OpenClaw src/test-utils/node-process.ts

Execute JavaScript source in a child Node.js process.
Useful for testing Node-specific behavior from Python.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def create_node_eval_args(
    source: str,
    eval_flag: str = "--eval",
    imports: list[str] | None = None,
) -> list[str]:
    """Build command-line args for running Node.js with inline source."""
    args: list[str] = []
    if imports:
        for specifier in imports:
            args.extend(["--import", specifier])
    args.extend(["--input-type=module", eval_flag, source])
    return args


def exec_node_eval_sync(
    source: str,
    eval_flag: str = "--eval",
    imports: list[str] | None = None,
    cwd: str | None = None,
    timeout: float | None = 30,
) -> str:
    """Execute a Node.js script string and return stdout."""
    import shutil
    node_path = shutil.which("node") or "node"
    args = [node_path] + create_node_eval_args(source, eval_flag, imports)
    result = subprocess.run(
        args,
        cwd=cwd or ".",
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Node eval failed (exit {result.returncode}): {result.stderr}"
        )
    return result.stdout


def spawn_node_eval_sync(
    source: str,
    eval_flag: str = "--eval",
    imports: list[str] | None = None,
    cwd: str | None = None,
    timeout: float | None = 30,
) -> subprocess.CompletedProcess[str]:
    """Execute a Node.js script string and return the full CompletedProcess."""
    import shutil
    node_path = shutil.which("node") or "node"
    args = [node_path] + create_node_eval_args(source, eval_flag, imports)
    return subprocess.run(
        args,
        cwd=cwd or ".",
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def node_eval_json(
    source: str,
    eval_flag: str = "--eval",
    imports: list[str] | None = None,
    cwd: str | None = None,
) -> object:
    """Execute a Node.js script that prints JSON, and parse the result."""
    output = exec_node_eval_sync(source, eval_flag, imports, cwd)
    # Find the last line that looks like JSON
    for line in reversed(output.strip().splitlines()):
        line = line.strip()
        if line and (line.startswith("{") or line.startswith("[")):
            return json.loads(line)
    raise ValueError(f"No JSON found in Node output: {output[:200]}")
