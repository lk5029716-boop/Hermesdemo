"""
wizard_session.py — Step-by-step wizard session with deferred answers.

Adapted from OpenClaw src/wizard/session.ts (WizardSession).

Hermes has gateway/session.py for message sessions but lacks the
wizard-specific step-by-step session model where the wizard runner
and UI client are decoupled via a deferred answer queue.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from .wizard_prompts import WizardPrompter, WizardProgress, WizardCancelledError


class WizardStep:
    """A single step in the wizard session."""
    def __init__(
        self,
        step_id: str,
        step_type: str,  # "note", "select", "text", "confirm", "multiselect", "progress", "action"
        title: str | None = None,
        message: str | None = None,
        format: str | None = None,
        options: list[dict] | None = None,
        initial_value: Any = None,
        placeholder: str | None = None,
        sensitive: bool = False,
        executor: str = "client",
    ):
        self.id = step_id
        self.type = step_type
        self.title = title
        self.message = message
        self.format = format
        self.options = options or []
        self.initial_value = initial_value
        self.placeholder = placeholder
        self.sensitive = sensitive
        self.executor = executor


WizardSessionStatus = str  # "running" | "done" | "cancelled" | "error"


class WizardNextResult:
    """Result from next() — either a step to show or terminal state."""
    def __init__(self, done: bool, step: WizardStep | None = None,
                 status: WizardSessionStatus = "running", error: str | None = None):
        self.done = done
        self.step = step
        self.status = status
        self.error = error


class WizardSession:
    """
    Decouples the wizard runner from the UI client.

    The wizard runner calls prompter methods which enqueue steps.
    The UI client calls next() to get the next step to display,
    then answer() to provide the user's response.
    """

    def __init__(self, runner: callable):
        self._runner = runner
        self._current_step: WizardStep | None = None
        self._step_future: asyncio.Future | None = None
        self._answer_futures: dict[str, asyncio.Future] = {}
        self._status: WizardSessionStatus = "running"
        self._error: str | None = None
        self._pending_terminal = False

        # Start the runner
        prompter = _SessionPrompter(self)
        asyncio.ensure_future(self._run(prompter))

    async def next(self) -> WizardNextResult:
        """Get the next step to display, or terminal result."""
        if self._current_step:
            return WizardNextResult(done=False, step=self._current_step, status=self._status)

        if self._pending_terminal:
            self._pending_terminal = False
            return WizardNextResult(done=True, status=self._status, error=self._error)

        if self._status != "running":
            return WizardNextResult(done=True, status=self._status, error=self._error)

        if not self._step_future:
            self._step_future = asyncio.get_event_loop().create_future()

        step = await self._step_future
        if step:
            return WizardNextResult(done=False, step=step, status=self._status)
        return WizardNextResult(done=True, status=self._status, error=self._error)

    async def answer(self, step_id: str, value: Any) -> None:
        """Provide an answer for a pending step."""
        fut = self._answer_futures.get(step_id)
        if not fut:
            raise RuntimeError("wizard: no pending step")
        del self._answer_futures[step_id]
        self._current_step = None
        fut.set_result(value)

    def cancel(self) -> None:
        """Cancel the wizard session."""
        if self._status != "running":
            return
        self._status = "cancelled"
        self._error = "cancelled"
        self._current_step = None
        for fut in self._answer_futures.values():
            fut.cancel()
        self._answer_futures.clear()
        self._resolve_step(None)

    def push_step(self, step: WizardStep) -> None:
        """Push a step to be displayed."""
        self._current_step = step
        self._resolve_step(step)

    async def _run(self, prompter: _SessionPrompter) -> None:
        """Run the wizard and handle completion/errors."""
        try:
            await self._runner(prompter)
            self._status = "done"
        except WizardCancelledError as e:
            self._status = "cancelled"
            self._error = str(e)
        except Exception as e:
            self._status = "error"
            self._error = str(e)
        finally:
            self._resolve_step(None)

    async def await_answer(self, step: WizardStep) -> Any:
        """Wait for the user to answer a step."""
        if self._status != "running":
            raise RuntimeError("wizard: session not running")
        self.push_step(step)
        fut = asyncio.get_event_loop().create_future()
        self._answer_futures[step.id] = fut
        return await fut

    def _resolve_step(self, step: WizardStep | None) -> None:
        """Resolve the current step future."""
        if not self._step_future:
            if step is None:
                self._pending_terminal = True
            return
        fut = self._step_future
        self._step_future = None
        fut.set_result(step)

    @property
    def status(self) -> WizardSessionStatus:
        return self._status

    @property
    def error(self) -> str | None:
        return self._error


class _SessionPrompter:
    """Prompter that enqueues steps into a WizardSession instead of blocking."""

    def __init__(self, session: WizardSession):
        self._session = session

    async def intro(self, title: str) -> None:
        await self._prompt(WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="note",
            title=title,
            message="",
            executor="client",
        ))

    async def outro(self, message: str) -> None:
        await self._prompt(WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="note",
            title="Done",
            message=message,
            executor="client",
        ))

    async def note(self, message: str, title: str | None = None) -> None:
        await self._prompt(WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="note",
            title=title,
            message=message,
            executor="client",
        ))

    async def plain(self, message: str) -> None:
        await self._prompt(WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="note",
            message=message,
            format="plain",
            executor="client",
        ))

    async def select(self, params: dict) -> Any:
        step = WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="select",
            message=params["message"],
            options=params.get("options", []),
            initial_value=params.get("initial_value"),
            executor="client",
        )
        return await self._prompt(step)

    async def multiselect(self, params: dict) -> list:
        step = WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="multiselect",
            message=params["message"],
            options=params.get("options", []),
            initial_value=params.get("initial_values"),
            executor="client",
        )
        result = await self._prompt(step)
        return result if isinstance(result, list) else []

    async def text(self, params: dict) -> str:
        step = WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="text",
            message=params["message"],
            initial_value=params.get("initial_value"),
            placeholder=params.get("placeholder"),
            sensitive=params.get("sensitive", False),
            executor="client",
        )
        result = await self._prompt(step)
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, (int, float, bool)):
            return str(result)
        return ""

    async def confirm(self, params: dict) -> bool:
        step = WizardStep(
            step_id=str(uuid.uuid4()),
            step_type="confirm",
            message=params["message"],
            initial_value=params.get("initial_value"),
            executor="client",
        )
        return bool(await self._prompt(step))

    def progress(self, label: str) -> WizardProgress:
        return WizardProgress(label=label)

    async def _prompt(self, step: WizardStep) -> Any:
        return await self._session.await_answer(step)
