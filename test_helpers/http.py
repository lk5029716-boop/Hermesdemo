"""HTTP test helpers.

Ported from OpenClaw src/test-helpers/http.ts
"""

from __future__ import annotations

import json
from typing import Any


def json_response(body: Any, status: int = 200) -> dict[str, Any]:
    """Create a JSON HTTP response dict (for test mocks)."""
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def request_url(input: str) -> str:
    """Extract a URL string from various request-like inputs."""
    return str(input)


def request_body_text(body: str | None | Any) -> str:
    """Safely extract a text body, defaulting to '{}'."""
    return body if isinstance(body, str) else "{}"
