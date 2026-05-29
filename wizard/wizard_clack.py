"""
wizard_clack.py — Terminal prompter using interactive selection.

Adapted from OpenClaw src/wizard/clack-prompter.ts.

Provides a structured prompter interface for the setup wizard with
searchable select, multiselect, text input, confirm, and progress.
This adapts the OpenClaw clack-based approach to use Hermes's
existing prompt toolkit (curses_ui, prompt helpers).
"""

from __future__ import annotations

import re
import sys
from typing import Any, Optional, TypeVar

T = TypeVar("T")


def _normalize_search_tokens(search: str) -> list[str]:
    """Split search string into normalized lowercase tokens."""
    normalized = (search or "").strip().lower()
    tokens = re.split(r"\s+", normalized)
    return [t for t in tokens if t]


def _build_option_search_text(label: str, hint: str = "", value: str = "") -> str:
    """Build searchable text from option components."""
    return f"{label} {hint} {value}".strip().lower()


def tokenized_search_filter(search: str, label: str, hint: str = "", value: str = "") -> bool:
    """Filter function for tokenized search matching."""
    tokens = _normalize_search_tokens(search)
    if not tokens:
        return True
    haystack = _build_option_search_text(label, hint, value)
    return all(token in haystack for token in tokens)


class WizardClackPrompter:
    """
    Terminal prompter for the setup wizard.

    Adapts OpenClaw's clack-based prompts to use Hermes's existing
    curses UI (curses_radiolist, curses_checklist) and prompt helpers.
    """

    def __init__(self):
        self._is_tty = hasattr(sys.stdin, "isatty") and sys.stdin.isatty()

    def intro(self, title: str) -> None:
        """Show wizard intro banner."""
        from hermes_cli.colors import Colors, color
        print()
        print(color(f"◆ {title}", Colors.CYAN, Colors.BOLD))
        print()

    def outro(self, message: str) -> None:
        """Show wizard outro."""
        from hermes_cli.colors import Colors, color
        print()
        print(color(f"✓ {message}", Colors.GREEN, Colors.BOLD))

    def note(self, message: str, title: str | None = None) -> None:
        """Show a note/info message."""
        from hermes_cli.colors import Colors, color
        if title:
            print()
            print(color(f"─── {title} ───", Colors.CYAN))
        for line in message.split("\n"):
            print(f"  {line}")
        print()

    def plain(self, message: str) -> None:
        """Print a plain message."""
        if not message.endswith("\n"):
            message += "\n"
        sys.stdout.write(message)

    def select(self, message: str, options: list[dict[str, T]],
               initial: T | None = None, searchable: bool = False) -> T:
        """
        Single-select from a list of options.
        Options: [{"value": ..., "label": ..., "hint": ...}]
        """
        if not self._is_tty:
            # Non-interactive: return initial or first option
            if initial is not None:
                return initial
            return options[0]["value"]

        labels = [opt.get("label", str(opt.get("value", ""))) for opt in options]

        try:
            from hermes_cli.curses_ui import curses_radiolist
            idx = curses_radiolist(message, labels, selected=0)
            if idx >= 0:
                return options[idx]["value"]
        except Exception:
            pass

        # Fallback to numbered input
        from hermes_cli.colors import Colors, color
        print(color(f"  {message}", Colors.YELLOW))
        for i, opt in enumerate(options):
            marker = "●" if opt.get("value") == initial else "○"
            hint_str = f" ({opt['hint']})" if opt.get("hint") else ""
            style = Colors.GREEN if opt.get("value") == initial else None
            print(color(f"  {marker} {opt['label']}{hint_str}", style))

        while True:
            try:
                raw = input(color(f"  Select [1-{len(options)}]: ", Colors.DIM))
                if not raw and initial is not None:
                    return initial
                idx = int(raw) - 1
                if 0 <= idx < len(options):
                    return options[idx]["value"]
            except (ValueError, EOFError, KeyboardInterrupt):
                if initial is not None:
                    return initial
                raise

    def multiselect(self, message: str, options: list[dict[str, T]],
                    initial: list[T] | None = None, searchable: bool = False) -> list[T]:
        """
        Multi-select from a list of options.
        Returns list of selected values.
        """
        if not self._is_tty:
            return initial or []

        labels = [opt.get("label", str(opt.get("value", ""))) for opt in options]
        pre_selected = set()
        if initial:
            for i, opt in enumerate(options):
                if opt.get("value") in initial:
                    pre_selected.add(i)

        try:
            from hermes_cli.curses_ui import curses_checklist
            chosen = curses_checklist(message, labels, pre_selected)
            return [options[i]["value"] for i in sorted(chosen)]
        except Exception:
            pass

        # Fallback: space-separated indices
        from hermes_cli.colors import Colors, color
        print(color(f"  {message}", Colors.YELLOW))
        for i, opt in enumerate(options):
            print(f"  [{i + 1}] {opt.get('label', str(opt.get('value', '')))}")

        while True:
            try:
                raw = input(color(f"  Select (comma-separated, empty for none): ", Colors.DIM))
                if not raw:
                    return initial or []
                indices = [int(x.strip()) - 1 for x in raw.split(",")]
                return [options[i]["value"] for i in indices if 0 <= i < len(options)]
            except (ValueError, EOFError, KeyboardInterrupt):
                return initial or []

    def text(self, message: str, initial: str = "", placeholder: str = "",
             validate=None, sensitive: bool = False) -> str:
        """Text input with optional validation and masking."""
        from hermes_cli.colors import Colors, color

        while True:
            try:
                if sensitive:
                    import getpass
                    display = f"  {message}: "
                    value = getpass.getpass(color(display, Colors.YELLOW))
                else:
                    hint = f" [{initial}]" if initial else f" [{placeholder}]" if placeholder else ""
                    raw = input(color(f"  {message}{hint}: ", Colors.YELLOW))
                    value = raw or initial or placeholder or ""

                if validate:
                    error = validate(value)
                    if error:
                        print(color(f"  ✗ {error}", Colors.RED))
                        continue

                return value
            except (EOFError, KeyboardInterrupt):
                return initial or ""

    def confirm(self, message: str, default: bool = True) -> bool:
        """Yes/no confirmation."""
        from hermes_cli.colors import Colors, color
        default_str = "Y/n" if default else "y/N"

        while True:
            try:
                raw = input(color(f"  {message} [{default_str}]: ", Colors.YELLOW)).strip().lower()
                if not raw:
                    return default
                if raw in ("y", "yes"):
                    return True
                if raw in ("n", "no"):
                    return False
                print(color("  Please enter 'y' or 'n'", Colors.RED))
            except (EOFError, KeyboardInterrupt):
                return default

    def progress(self, label: str) -> "WizardProgress":
        """Create a progress indicator."""
        return WizardProgress(label)


class WizardProgress:
    """Simple progress indicator for long-running wizard steps."""

    def __init__(self, label: str):
        self.label = label
        from hermes_cli.colors import Colors, color
        print(color(f"  ⏳ {label}...", Colors.YELLOW))

    def update(self, message: str) -> None:
        from hermes_cli.colors import Colors, color
        print(color(f"  ⏳ {message}...", Colors.YELLOW))

    def stop(self, message: str | None = None) -> None:
        from hermes_cli.colors import Colors, color
        if message:
            print(color(f"  ✓ {message}", Colors.GREEN))
        else:
            print(color(f"  ✓ Done", Colors.GREEN))
