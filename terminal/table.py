"""Table rendering for terminal output.

Ported from OpenClaw src/terminal/table.ts

Simplified port — renders ASCII/Unicode tables with column alignment,
width constraints, and ANSI-aware text wrapping.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Literal

from .ansi import strip_ansi, visible_width


type Align = Literal["left", "right", "center"]


@dataclass
class TableColumn:
    key: str
    header: str
    align: Align = "left"
    min_width: int = 3
    max_width: int | None = None
    flex: bool = False


@dataclass
class RenderTableOptions:
    columns: list[TableColumn]
    rows: list[dict[str, str]]
    width: int | None = None
    padding: int = 1
    border: Literal["unicode", "ascii", "none"] = "unicode"


def _display_string(value: str) -> str:
    """Convert a value to a display-safe string."""
    if not isinstance(value, str):
        return str(value)
    return value.strip()


def _resolve_default_border() -> Literal["unicode", "ascii"]:
    """Determine default border style based on platform/terminal."""
    if sys.platform == "win32":
        term = os.environ.get("TERM", "")
        term_program = os.environ.get("TERM_PROGRAM", "")
        is_modern = (
            bool(os.environ.get("WT_SESSION"))
            or "xterm" in term
            or "cygwin" in term
            or "msys" in term
            or term_program == "vscode"
        )
        return "unicode" if is_modern else "ascii"
    return "unicode"


def _repeat(ch: str, n: int) -> str:
    return ch * max(0, n)


def _pad_cell(text: str, width: int, align: Align) -> str:
    w = visible_width(text)
    if w >= width:
        return text
    pad = width - w
    if align == "right":
        return f"{_repeat(' ', pad)}{text}"
    if align == "center":
        left = pad // 2
        return f"{_repeat(' ', left)}{text}{_repeat(' ', pad - left)}"
    return f"{text}{_repeat(' ', pad)}"


def _get_terminal_table_width(min_width: int = 60, fallback_width: int = 120) -> int:
    """Get terminal width for table rendering."""
    cols = getattr(sys.stdout, "columns", None) if hasattr(sys.stdout, "columns") else None  # type: ignore[union-attr]
    return max(min_width, cols or fallback_width)


def render_table(opts: RenderTableOptions) -> str:
    """Render a table as a formatted string.

    Supports unicode/ascii/none borders, column alignment, width constraints,
    and flex columns.
    """
    columns = opts.columns
    rows = [{k: _display_string(v) for k, v in row.items()} for row in opts.rows]

    if opts.border == "none":
        header = " | ".join(c.header for c in columns)
        lines = [header] + [
            " | ".join(row.get(c.key, "") for c in columns) for row in rows
        ]
        return "\n".join(lines) + "\n"

    border = opts.border if opts.border != "unicode" else _resolve_default_border()
    padding = max(0, opts.padding)

    # Compute column metrics
    metrics = []
    for c in columns:
        header_w = visible_width(c.header)
        cell_w = max((visible_width(row.get(c.key, "")) for row in rows), default=0)
        metrics.append({"header_w": header_w, "cell_w": cell_w})

    # Compute widths
    widths: list[int] = []
    for i, c in enumerate(columns):
        base = max(metrics[i]["header_w"], metrics[i]["cell_w"]) + padding * 2
        if c.max_width is not None:
            base = min(base, c.max_width)
        widths.append(max(c.min_width, base))

    # Apply max_width constraint
    max_w = opts.width
    if max_w is not None and max_w > 0:
        total = sum(widths) + len(columns) + 1
        if total > max_w:
            over = total - max_w
            # Shrink flex columns first
            flex_order = sorted(
                [i for i, c in enumerate(columns) if c.flex],
                key=lambda i: widths[i],
                reverse=True,
            )
            non_flex_order = sorted(
                [i for i, c in enumerate(columns) if not c.flex],
                key=lambda i: widths[i],
                reverse=True,
            )

            for i in flex_order:
                if over <= 0:
                    break
                min_w = max(metrics[i]["header_w"] + padding * 2, 3)
                shrink = min(over, widths[i] - min_w)
                widths[i] -= shrink
                over -= shrink

            for i in non_flex_order:
                if over <= 0:
                    break
                min_w = max(metrics[i]["header_w"] + padding * 2, 3)
                shrink = min(over, widths[i] - min_w)
                widths[i] -= shrink
                over -= shrink

    # Border characters
    if border == "ascii":
        h_sep = "-"
        v_sep = "+"
        cross = "+"
    else:
        h_sep = "─"
        v_sep = "│"
        cross = "┼"

    h_line = cross.join(_repeat(h_sep, w + padding * 2) for w in widths)

    def format_row(values: list[str]) -> str:
        cells = [_pad_cell(v, w, c.align) for v, w, c in zip(values, widths, columns)]
        return f"{v_sep} " + f" {v_sep} ".join(cells) + f" {v_sep}"

    header_cells = [_pad_cell(c.header, widths[i], c.align) for i, c in enumerate(columns)]
    header_line = f"{v_sep} " + f" {v_sep} ".join(header_cells) + f" {v_sep}"

    lines: list[str] = []
    lines.append(h_line)
    lines.append(header_line)
    lines.append(h_line)
    for row in rows:
        vals = [row.get(c.key, "") for c in columns]
        lines.append(format_row(vals))
    lines.append(h_line)

    return "\n".join(lines) + "\n"
