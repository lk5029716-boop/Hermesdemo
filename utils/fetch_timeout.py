"""
fetch_timeout.py — HTTP fetch with timeout and URL safety.

Adapted from OpenClaw src/utils/fetch-timeout.ts.

Provides fetch with:
- Configurable timeout (deadline-based, not per-socket)
- URL sanitization (blocks private/internal IPs by default)
- SSRF protection
- Safe URL parsing
"""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse


class SSPRFError(Exception):
    """Raised when a URL points to an internal/restricted IP."""
    pass


class FetchTimeoutError(Exception):
    """Raised when a fetch times out."""
    pass


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    status: int
    status_text: str
    ok: bool
    url: str
    headers: dict[str, str]
    body: str = ""
    content_type: str | None = None
    elapsed_ms: float = 0.0

    def raise_for_status(self) -> None:
        if not self.ok:
            raise FetchTimeoutError(f"HTTP {self.status}: {self.status_text}")


def is_private_url(url: str) -> bool:
    """Check if a URL resolves to a private/internal IP (SSRF check)."""
    try:
        parsed = urlparse(url.strip())
        hostname = parsed.hostname or ""
        if not hostname:
            return False
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return True
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        # Not an IP, resolve DNS then check
        try:
            info = socket.getaddrinfo(hostname, None)
            for family, socktype, proto, canonname, sockaddr in info:
                try:
                    addr = ipaddress.ip_address(sockaddr[0])
                    if addr.is_private or addr.is_loopback or addr.is_reserved:
                        return True
                except ValueError:
                    continue
        except socket.gaierror:
            return True  # Can't resolve = treat as unsafe
    return False


def sanitize_url(url: str, allow_private: bool = False) -> str:
    """
    Sanitize a URL for safe fetching.

    Raises SSPRFError if URL points to private IP and allow_private is False.
    """
    url = url.strip()
    if not url:
        raise ValueError("Empty URL")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported scheme: {parsed.scheme}")

    if not allow_private and is_private_url(url):
        raise SSPRFError(f"URL resolves to private/internal IP: {url}")

    return url


async def fetch_with_timeout(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    timeout_ms: int = 30000,
    allow_private: bool = False,
) -> FetchResult:
    """
    Fetch a URL with timeout and SSRF protection.

    Args:
        url: URL to fetch
        method: HTTP method
        headers: Request headers
        body: Request body
        timeout_ms: Timeout in milliseconds
        allow_private: Allow private/internal IPs

    Returns:
        FetchResult with status, headers, body
    """
    import time
    import urllib.request
    import urllib.error

    safe_url = sanitize_url(url, allow_private=allow_private)
    timeout_sec = timeout_ms / 1000.0

    req = urllib.request.Request(
        safe_url,
        data=body.encode() if body else None,
        headers=headers or {},
        method=method,
    )

    start = time.monotonic()
    try:
        response = urllib.request.urlopen(req, timeout=timeout_sec)
        elapsed = (time.monotonic() - start) * 1000
        resp_body = response.read().decode("utf-8", errors="replace")
        resp_headers = dict(response.headers)
        return FetchResult(
            status=response.status,
            status_text=response.reason,
            ok=200 <= response.status < 300,
            url=safe_url,
            headers=resp_headers,
            body=resp_body,
            content_type=resp_headers.get("Content-Type"),
            elapsed_ms=elapsed,
        )
    except urllib.error.HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        return FetchResult(
            status=e.code,
            status_text=e.reason,
            ok=False,
            url=safe_url,
            headers=dict(e.headers) if e.headers else {},
            elapsed_ms=elapsed,
        )
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        elapsed = (time.monotonic() - start) * 1000
        raise FetchTimeoutError(f"Fetch timed out after {timeout_ms}ms: {e}") from e
