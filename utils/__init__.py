"""
utils — Generic utility modules.

Adapted from OpenClaw src/utils/ (9 files selected from 26 total).

These are pure utility functions with no OpenClaw dependencies.
They fill gaps in Hermes's existing utils.py.
"""

from .chunk_items import chunk_items
from .cjk_chars import is_cjk_char, has_cjk, count_cjk_chars, estimate_tokens, split_cjk_aware
from .run_with_concurrency import run_with_concurrency
from .queue_helpers import AsyncDropQueue, QueueConfig, QueueStats, DropPolicy, QueueFull
from .fetch_timeout import fetch_with_timeout, sanitize_url, is_private_url, FetchResult, SSPRFError, FetchTimeoutError
from .timer_delay import safe_delay, delayed_iterate, timeout_guard
from .transcript_tools import extract_tool_calls, extract_tool_results, has_tool_calls, is_tool_result, ToolCall, ToolResult
from .reaction_level import get_reaction_level, emoji_from_level, should_highlight, ReactionLevel, ReactionCategory
from .directive_tags import parse_directives, has_directive, get_directive_value, strip_directives, DirectiveParseResult, ParsedDirective

__all__ = [
    "chunk_items",
    "is_cjk_char", "has_cjk", "count_cjk_chars", "estimate_tokens", "split_cjk_aware",
    "run_with_concurrency",
    "AsyncDropQueue", "QueueConfig", "QueueStats", "DropPolicy", "QueueFull",
    "fetch_with_timeout", "sanitize_url", "is_private_url", "FetchResult", "SSPRFError", "FetchTimeoutError",
    "safe_delay", "delayed_iterate", "timeout_guard",
    "extract_tool_calls", "extract_tool_results", "has_tool_calls", "is_tool_result", "ToolCall", "ToolResult",
    "get_reaction_level", "emoji_from_level", "should_highlight", "ReactionLevel", "ReactionCategory",
    "parse_directives", "has_directive", "get_directive_value", "strip_directives", "DirectiveParseResult", "ParsedDirective",
]
