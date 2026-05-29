"""Security utilities — secret comparison, safe regex, path scanning, external content.

Ported from OpenClaw src/security/
"""

from .external_content import (
    EXTERNAL_CONTENT_SECURITY_WARNING,
    ExternalContentSource,
    build_safe_external_prompt,
    detect_suspicious_patterns,
    sanitize_external_content_text,
    wrap_external_content,
)
from .safe_regex_scan import (
    SafeRegexReplacer,
    has_path_traversal,
    is_path_inside,
    is_path_within_any,
    is_safe_pattern,
    safe_resolve_path,
)
from .secret_equal import safe_string_equals

__all__ = [
    "EXTERNAL_CONTENT_SECURITY_WARNING",
    "ExternalContentSource",
    "SafeRegexReplacer",
    "build_safe_external_prompt",
    "detect_suspicious_patterns",
    "has_path_traversal",
    "is_path_inside",
    "is_path_within_any",
    "is_safe_pattern",
    "safe_resolve_path",
    "safe_string_equals",
    "sanitize_external_content_text",
    "wrap_external_content",
]
