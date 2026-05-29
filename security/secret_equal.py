"""Secret equality comparison — timing-safe string comparison.

Ported from OpenClaw src/security/secret-equal.ts

Uses hmac to prevent timing attacks when comparing secrets.
"""

from __future__ import annotations

import hashlib
import hmac


def safe_string_equals(left: str, right: str) -> bool:
    """Timing-safe string comparison of sensitive values.

    Uses double-HMAC pattern to prevent timing attacks regardless
    of whether the lengths match.
    """
    left_bytes = left.encode("utf8")
    right_bytes = right.encode("utf8")
    key = b"openclaw-secret-equal-v1"
    return hmac.new(key, left_bytes, hashlib.sha256).digest() == hmac.new(
        key, right_bytes, hashlib.sha256
    ).digest()
