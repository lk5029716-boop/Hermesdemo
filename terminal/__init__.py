"""Terminal/CLI rendering utilities.

Ported from OpenClaw src/terminal/

Provides ANSI escape handling, text width calculation, table rendering,
OSC hyperlinks, progress indicators, and prompt styling.
"""

from .ansi import sanitize_for_log, strip_ansi, visible_width
from .osc_progress import OscProgressState, create_osc_progress_controller, supports_osc_progress
from .palette import LOBSTER_PALETTE
from .progress_line import clear_active_progress_line, register_active_progress_line, unregister_active_progress_line
from .prompt_style import colorize, is_rich, style_prompt_hint, style_prompt_message, style_prompt_title
from .safe_text import sanitize_terminal_text
from .table import TableColumn, RenderTableOptions, render_table
from .terminal_link import format_terminal_link

__all__ = [
    "LOBSTER_PALETTE",
    "OscProgressState",
    "RenderTableOptions",
    "TableColumn",
    "clear_active_progress_line",
    "colorize",
    "create_osc_progress_controller",
    "format_terminal_link",
    "is_rich",
    "register_active_progress_line",
    "render_table",
    "sanitize_for_log",
    "sanitize_terminal_text",
    "strip_ansi",
    "style_prompt_hint",
    "style_prompt_message",
    "style_prompt_title",
    "supports_osc_progress",
    "unregister_active_progress_line",
    "visible_width",
]
