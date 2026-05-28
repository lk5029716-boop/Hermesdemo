"""
wizard_session.py — Adapter from OpenClaw src/wizard/session.ts

Provides:
  - WizardStep: a single step in the wizard session
  - WizardSession: manages step-by-step wizard flow with deferred answers
  - WizardSessionStatus: running | done | cancelled | error

In OpenClaw this uses async IPC between gateway and client.
In Hermes this is used for the setup-wizard CLI flow where the
gateway drives the terminal directly.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from gateway.wizard_prompts import WizardCancelledError, WizardPrompter


@dataclass
class WizardStep:
    """A single step presented to the user.

    Adapted from WizardStep in src/wizard/session.ts.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "note"  # note | select | text | confirm | multiselect | progress | action
    title: Optional[str] = None
    message: Optional[str] = None
    format: Optional[str] = None  # "plain"
    options: Optional[list] = None
    initial_value: Any = None
    placeholder: Optional[str] = None
    sensitive: bool = False
    executor: str = "client"  # "gateway" | "client"


WizardSessionStatus = str  # "running" | "done" | "cancelled" | "error"


class WizardSession:
    """Step-based wizard session.

    The wizard flow (setup wizard) runs as a coroutine and pushes steps.
    The caller (terminal prompter) reads steps one at a time and
    provides answers.

    Adapted from WizardSession in src/wizard/session.ts.
    Uses asyncio Deferreds instead of JS promises.
    """

    def __init__(self, runner: Callable[[WizardPrompter], Any]):
        self._runner = runner
        self._current_step: Optional[WizardStep] = None
        self._step_future: Optional[asyncio.Future] = None
        self._pending_terminal_resolution = False
        self._answer_futures: Dict[str, asyncio.Future] = {}
        self._status: WizardSessionStatus = "running"
        self._error: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the wizard runner in the background."""
        self._task = asyncio.ensure_future(self._run())

    async def _run(self) -> None:
        """Internal — executes the runner and catches errors."""
        try:
            from gateway.wizard_prompts import TerminalPrompter
            prompter = SessionPrompter(self)
            await self._runner(prompter)
            self._status = "done"
        except WizardCancelledError as exc:
            self._status = "cancelled"
            self._error = str(exc)
        except Exception as exc:
            self._status = "error"
            self._error = str(exc)
        finally:
            self._resolve_step(None)

    async def next_step(self) -> Optional[WizardStep]:
        """Get the next step, or None if the session is done.

        Returns a dict-like step object or None.
        """
        if self._current_step is not None:
            step = self._current_step
            self._current_step = None
            return step
        if self._pending_terminal_resolution:
            self._pending_terminal_resolution = False
            return None
        if self._status != "running":
            return None
        loop = asyncio.get_event_loop()
        self._step_future = loop.create_future()
        step = await self._step_future
        return step

    async def answer(self, step_id: str, value: Any) -> None:
        """Provide an answer for a given step."""
        fut = self._answer_futures.pop(step_id, None)
        if fut is None:
            raise RuntimeError("wizard: no pending step")
        self._current_step = None
        fut.set_result(value)

    def cancel(self) -> None:
        """Cancel the session."""
        if self._status != "running":
            return
        self._status = "cancelled"
        self._error = "cancelled"
        self._current_step = None
        for fut in self._answer_futures.values():
            fut.set_exception(WizardCancelledError())
        self._answer_futures.clear()
        self._resolve_step(None)
        if self._task and not self._task.done():
            self._task.cancel()

    def _push_step(self, step: WizardStep) -> None:
        self._current_step = step
        self._resolve_step(step)

    def _resolve_step(self, step: Optional[WizardStep]) -> None:
        if self._step_future is None:
            if step is None:
                self._pending_terminal_resolution = True
            return
        fut = self._step_future
        self._step_future = None
        fut.set_result(step)

    async def _await_answer(self, step: WizardStep) -> Any:
        """Push a step and wait for the answer. Called by SessionPrompter."""
        if self._status != "running":
            raise RuntimeError("wizard: session not running")
        self._push_step(step)
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._answer_futures[step.id] = fut
        return await fut

    @property
    def status(self) -> WizardSessionStatus:
        return self._status

    @property
    def error(self) -> Optional[str]:
        return self._error


class SessionPrompter:
    """Bridge between WizardSession and the terminal.

    Maps WizardPrompter calls to WizardSession._await_answer.
    """

    def __init__(self, session: WizardSession):
        self._session = session

    async def intro(self, title: str) -> None:
        await self._prompt({"type": "note", "title": title, "message": "", "executor": "client"})

    async def outro(self, message: str) -> None:
        await self._prompt({"type": "note", "title": "Done", "message": message, "executor": "client"})

    async def note(self, message: str, title: Optional[str] = None) -> None:
        await self._prompt({"type": "note", "title": title, "message": message, "executor": "client"})

    async def plain(self, message: str) -> None:
        await self._prompt({"type": "note", "message": message, "format": "plain", "executor": "client"})

    async def select(self, *, message: str, options: list, initial_value=None, searchable=False):
        opts = [{"value": o.value, "label": o.label, "hint": o.hint} for o in options]
        res = await self._prompt({
            "type": "select",
            "message": message,
            "options": opts,
            "initial_value": initial_value,
            "executor": "client",
        })
        return res

    async def multiselect(self, *, message: str, options: list, initial_values=None, searchable=False):
        opts = [{"value": o.value, "label": o.label, "hint": o.hint} for o in options]
        res = await self._prompt({
            "type": "multiselect",
            "message": message,
            "options": opts,
            "initial_value": initial_values,
            "executor": "client",
        })
        return res if isinstance(res, list) else []

    async def text(self, *, message: str, initial_value=None, placeholder=None, validate=None, sensitive=False):
        res = await self._prompt({
            "type": "text",
            "message": message,
            "initial_value": initial_value,
            "placeholder": placeholder,
            "sensitive": sensitive,
            "executor": "client",
        })
        value = str(res) if res is not None else ""
        error = validate(value) if validate else None
        if error:
            raise ValueError(error)
        return value

    async def confirm(self, *, message: str, initial_value=None):
        res = await self._prompt({
            "type": "confirm",
            "message": message,
            "initial_value": initial_value,
            "executor": "client",
        })
        return bool(res)

    async def progress(self, label: str):
        from gateway.wizard_prompts import TerminalProgress
        return TerminalProgress(label)

    async def _prompt(self, step_data: dict) -> Any:
        step = WizardStep(**step_data)
        return await self._session._await_answer(step)
