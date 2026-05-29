"""Shared utility modules.

Ported from OpenClaw src/shared/

Core utilities that have no OpenClaw-internal dependencies:
    - String coercion and normalization
    - Record/dict coercion
    - Number coercion
    - Lazy promise loading
    - Listener notification
    - Balanced JSON extraction
    - Chat content extraction
    - Human list formatting
    - Entry metadata resolution
    - Message content block visitor
    - Regex escape
"""

from .balanced_json import BalancedJsonFragment, extract_balanced_json_prefix, extract_balanced_json_fragments
from .chat_content import coerce_chat_content_text, extract_text_from_chat_content
from .entry_metadata import resolve_emoji_and_homepage
from .human_list import format_human_list
from .lazy_promise import LazyPromiseLoader, create_lazy_promise_loader
from .listeners import notify_listeners, register_listener
from .message_content_blocks import visit_object_content_blocks
from .number_coerce import as_finite_number, as_positive_safe_integer, as_safe_integer_in_range, parse_finite_number
from .record_coerce import as_nullable_record, as_optional_record, is_record, read_string_field
from .regexp import escape_regexp
from .string_coerce import (
    has_nonempty_string,
    lowercase_preserving_whitespace,
    normalize_fast_mode,
    normalize_nullable_string,
    normalize_optional_string,
    read_string_value,
    resolve_primary_string_value,
)
from .string_normalization import (
    normalize_csv_or_loose_string_list,
    normalize_optional_lowercase_string,
    normalize_optional_trimmed_string_list,
    normalize_single_or_trimmed_string_list,
    normalize_sorted_unique_string_entries,
    normalize_string_entries,
    sort_unique_strings,
    unique_strings,
    unique_values,
)

__all__ = [
    # String coerce
    "has_nonempty_string",
    "lowercase_preserving_whitespace",
    "normalize_fast_mode",
    "normalize_nullable_string",
    "normalize_optional_string",
    "read_string_value",
    "resolve_primary_string_value",
    # String normalization
    "normalize_csv_or_loose_string_list",
    "normalize_optional_lowercase_string",
    "normalize_optional_trimmed_string_list",
    "normalize_single_or_trimmed_string_list",
    "normalize_sorted_unique_string_entries",
    "normalize_string_entries",
    "sort_unique_strings",
    "unique_strings",
    "unique_values",
    # Record coerce
    "as_nullable_record",
    "as_optional_record",
    "is_record",
    "read_string_field",
    # Number coerce
    "as_finite_number",
    "as_positive_safe_integer",
    "as_safe_integer_in_range",
    "parse_finite_number",
    # Lazy promise
    "LazyPromiseLoader",
    "create_lazy_promise_loader",
    # Listeners
    "notify_listeners",
    "register_listener",
    # Balanced JSON
    "BalancedJsonFragment",
    "extract_balanced_json_prefix",
    "extract_balanced_json_fragments",
    # Chat content
    "coerce_chat_content_text",
    "extract_text_from_chat_content",
    # Human list
    "format_human_list",
    # Entry metadata
    "resolve_emoji_and_homepage",
    # Message content blocks
    "visit_object_content_blocks",
    # Regexp
    "escape_regexp",
]
