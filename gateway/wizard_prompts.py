"""
wizard_prompts.py — Adapter from OpenClaw src/wizard/prompts.ts + clack-prompter.ts

Provides:
  - WizardPrompter protocol (interface)
  - WizardCancelledError
  - TerminalPrompter implementation using prompt_toolkit + Rich (Hermes-native)
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Protocol, Tuple


class WizardCancelledError(Exception):
    """Raised when the user cancels a wizard prompt (e.g. Ctrl+C)."""

    def __init__(self, message: str = "wizard cancelled"):
        super().__init__(message)
        self.name = "WizardCancelledError"


class WizardSelectOption:
    """A single option in a select / multiselect prompt."""

    def __init__(self, value: Any, label: str, hint: Optional[str] = None):
        self.value = value
        self.label = label
        self.hint = hint


class WizardPrompter(Protocol):
    """Interface that all wizard prompters must satisfy.

    Adapted from OpenClaw's src/wizard/prompts.ts WizardPrompter type.
    Hermes uses Rich + prompt_toolkit instead of @clack/prompts.
    """

    async def intro(self, title: str) -> None:
        """Display an intro / welcome banner."""
        ...

    async def outro(self, message: str) -> None:
        """Display a closing / completion message."""
        ...

    async def note(self, message: str, title: Optional[str] = None) -> None:
        """Display an informational note / notice."""
        ...

    async def plain(self, message: str) -> None:
        """Display plain unformatted text."""
        ...

    async def select(
        self,
        *,
        message: str,
        options: List[WizardSelectOption],
        initial_value: Optional[Any] = None,
        searchable: bool = False,
    ) -> Any:
        """Single-choice selection. Returns the selected option's value."""
        ...

    async def multiselect(
        self,
        *,
        message: str,
        options: List[WizardSelectOption],
        initial_values: Optional[List[Any]] = None,
        searchable: bool = False,
    ) -> List[Any]:
        """Multi-choice selection. Returns list of selected option values."""
        ...

    async def text(
        self,
        *,
        message: str,
        initial_value: Optional[str] = None,
        placeholder: Optional[str] = None,
        validate: Optional[Callable[[str], Optional[str]]] = None,
        sensitive: bool = False,
    ) -> str:
        """Text input. Returns the entered string."""
        ...

    async def confirm(
        self,
        *,
        message: str,
        initial_value: Optional[bool] = None,
    ) -> bool:
        """Yes/no confirmation."""
        ...

    async def progress(self, label: str) -> "WizardProgress":
        """Create a progress indicator."""
        ...


class WizardProgress(Protocol):
    async def update(self, message: str) -> None:
        ...

    async def stop(self, message: Optional[str] = None) -> None:
        ...


class TerminalProgress:
    """Simple Rich-progress-based progress indicator."""

    def __init__(self, label: str):
        self._label = label

    async def update(self, message: str) -> None:
        try:
            from rich.console import Console
            Console().print(f"[bold cyan]┊[/bold cyan] {message}")
        except Exception:
            print(f"  {message}")

    async def stop(self, message: Optional[str] = None) -> None:
        if message:
            try:
                from rich.console import Console
                Console().print(f"[bold green]✔[/bold green] {message}")
            except Exception:
                print(f"  ✓ {message}")


class TerminalPrompter:
    """Hermes-native terminal prompter using Rich + prompt_toolkit.

    Implements the WizardPrompter protocol.
    Adapted from OpenClaw's clack-prompter.ts which uses @clack/prompts.
    """

    def __init__(self):
        try:
            from rich.console import Console
            self._console = Console()
        except ImportError:
            self._console = None

    def _print(self, text: str, style: Optional[str] = None) -> None:
        if self._console and style:
            self._console.print(text, style=style)
        elif self._console:
            self._console.print(text)
        else:
            print(text)

    async def intro(self, title: str) -> None:
        self._print("")
        self._print(f"[bold]{title}[/bold]", style=None)
        self._print("━" * min(len(title), 50))

    async def outro(self, message: str) -> None:
        self._print(f"[bold green]{message}[/bold green]")

    async def note(self, message: str, title: Optional[str] = None) -> None:
        if title:
            self._print(f"[bold yellow]▸ {title}[/bold yellow]")
        for line in message.split("\n"):
            self._print(f"  {line}")

    async def plain(self, message: str) -> None:
        print(message if message.endswith("\n") else f"{message}\n")

    async def select(
        self,
        *,
        message: str,
        options: List[WizardSelectOption],
        initial_value: Optional[Any] = None,
        searchable: bool = False,
    ) -> Any:
        # KeyboardInterrupt → WizardCancelledError (matches OpenClaw behaviour)
        try:
            self._print(f"[bold]{message}[/bold]")
            for i, opt in enumerate(options, 1):
                hint_str = f" — {opt.hint}" if opt.hint else ""
                marker = "◉" if opt.value == initial_value else "○"
                self._print(f"  {marker} {i}. {opt.label}{hint_str}")

            while True:
                choice = input("  Enter number: ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx].value
                except ValueError:
                    pass
                self._print("  Invalid choice, try again.", style="red")
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelledError()

    async def multiselect(
        self,
        *,
        message: str,
        options: List[WizardSelectOption],
        initial_values: Optional[List[Any]] = None,
        searchable: bool = False,
    ) -> List[Any]:
        try:
            self._print(f"[bold]{message}[/bold] (comma-separated numbers)")
            for i, opt in enumerate(options, 1):
                hint_str = f" — {opt.hint}" if opt.hint else ""
                marker = "◉" if initial_values and opt.value in initial_values else "○"
                self._print(f"  {marker} {i}. {opt.label}{hint_str}")

            while True:
                choice = input("  Enter numbers (e.g. 1,3): ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(",")]
                    results = []
                    for idx in indices:
                        if 0 <= idx < len(options):
                            results.append(options[idx].value)
                    return results
                except (ValueError, IndexError):
                    self._print("  Invalid choice, try again.", style="red")
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelledError()

    async def text(
        self,
        *,
        message: str,
        initial_value: Optional[str] = None,
        placeholder: Optional[str] = None,
        validate: Optional[Callable[[str], Optional[str]]] = None,
        sensitive: bool = False,
    ) -> str:
        try:
            hint = ""
            if placeholder:
                hint = f" [{placeholder}]"
            if initial_value and not sensitive:
                hint = f" [{initial_value}]"
            self._print(f"[bold]{message}{hint}[/bold]")

            get_input = input
            if sensitive:
                import getpass
                get_input = getpass.getpass

            while True:
                prompt_str = "  " + ("*" if sensitive else "> ")
                value = get_input(prompt_str).strip()
                if not value and initial_value is not None:
                    value = initial_value
                if validate:
                    error = validate(value)
                    if error:
                        self._print(f"  [red]{error}[/red]")
                        continue
                return value
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelledError()

    async def confirm(
        self,
        *,
        message: str,
        initial_value: Optional[bool] = None,
    ) -> bool:
        try:
            hint = " [Y/n]" if initial_value is not False else " [y/N]"
            self._print(f"[bold]{message}{hint}[/bold]")
            value = input("  > ").strip().lower()
            if not value:
                if initial_value is not None:
                    return initial_value
                return True
            return value in ("y", "yes", "true", "1")
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelledError()

    async def progress(self, label: str) -> WizardProgress:
        self._print(f"[bold cyan]┊ {label}[/bold cyan]")
        return TerminalProgress(label)
