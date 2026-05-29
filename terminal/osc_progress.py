"""OSC-9;4 terminal progress indicator.

Ported from OpenClaw src/terminal/osc-progress.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Protocol


class _OscProgressController(Protocol):
    def set_indeterminate(self, label: str) -> None: ...
    def set_percent(self, label: str, percent: int) -> None: ...
    def clear(self) -> None: ...


@dataclass
class OscProgressState:
    """Internal state for OSC progress tracking."""
    _write: Callable[[str], None]
    _enabled: bool
    _last_label: str = ""


_OSC_ST = "\x1b\\"
_OSC_BEL = "\x07"
_OSC_C1_ST = "\x9c"


def _sanitize_osc_label(label: str) -> str:
    """Remove dangerous characters from OSC progress labels."""
    return (
        label.replace(_OSC_ST, "")
        .replace(_OSC_BEL, "")
        .replace(_OSC_C1_ST, "")
        .replace("\x1b", "")
        .replace("]", "")
        .strip()
    )


def _format_osc_progress(state_code: int, percent: int | None, label: str) -> str:
    """Format an OSC 9;4 progress escape sequence."""
    clean = _sanitize_osc_label(label)
    if percent is None:
        return f"\x1b]9;4;{state_code};;{clean}{_OSC_ST}"
    normalized = max(0, min(100, round(percent)))
    return f"\x1b]9;4;{state_code};{normalized};{clean}{_OSC_ST}"


def supports_osc_progress(is_tty: bool) -> bool:
    """Check if the terminal supports OSC progress indicators."""
    if not is_tty:
        return False
    term_program = (os.environ.get("TERM_PROGRAM") or "").lower()
    term = (os.environ.get("TERM") or "").lower()
    return (
        "ghostty" in term_program
        or "wezterm" in term_program
        or "ghostty" in term
        or "wezterm" in term
        or bool(os.environ.get("WT_SESSION"))
    )


def create_osc_progress_controller(
    is_tty: bool,
    write: Callable[[str], None],
) -> OscProgressState:
    """Create an OSC progress controller."""
    enabled = supports_osc_progress(is_tty)

    state = OscProgressState(_write=write, _enabled=enabled)

    if not enabled:
        # Return a no-op controller
        return state

    # Bind methods via closure
    def set_indeterminate(label: str) -> None:
        state._last_label = label
        write(_format_osc_progress(3, None, label))

    def set_percent(label: str, percent: int) -> None:
        state._last_label = label
        write(_format_osc_progress(1, percent, label))

    def clear() -> None:
        write(_format_osc_progress(0, 0, state._last_label))

    # Attach methods
    state.set_indeterminate = set_indeterminate  # type: ignore[method-assign]
    state.set_percent = set_percent  # type: ignore[method-assign]
    state.clear = clear  # type: ignore[method-assign]

    return state
