"""
wizard_finalize.py — Setup finalization: health check, summary, next steps.

Adapted from OpenClaw src/wizard/setup.finalize.ts (finalizeSetupWizard).

OpenClaw finalize does:
  1. Systemd linger check (Linux)
  2. Daemon install / restart
  3. Gateway health check
  4. Control UI assets build
  5. Display gateway URLs + token
  6. Offer TUI vs web UI vs later

Hermes adaptation:
  - No systemd (cloud-native / Railway)
  - No daemon install (managed by Railway/PM2)
  - Keeps: health check, summary display, next steps
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from wizard_prompts import WizardPrompter

logger = logging.getLogger(__name__)


@dataclass
class FinalizeResult:
    """Result of the finalize step."""
    gateway_reachable: bool = False
    health_ok: bool = False
    launched_tui: bool = False
    urls: Dict[str, str] = None

    def __post_init__(self):
        if self.urls is None:
            self.urls = {}


async def run_health_check(
    gateway_url: str,
    token: Optional[str] = None,
    prompter: Optional[WizardPrompter] = None,
) -> bool:
    """Check if the gateway is reachable and healthy.

    Adapted from the health check portion of setup.finalize.ts.
    """
    import aiohttp

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{gateway_url}/health", headers=headers) as resp:
                ok = resp.status == 200
                if prompter:
                    if ok:
                        await prompter.note("Gateway is healthy ✓", "Health Check")
                    else:
                        await prompter.note(
                            f"Gateway returned status {resp.status}",
                            "Health Check",
                        )
                return ok
    except Exception as exc:
        logger.warning("Gateway health check failed: %s", exc)
        if prompter:
            await prompter.note(
                f"Gateway not reachable at {gateway_url}\n"
                f"Error: {exc}\n\n"
                f"Start the gateway first:\n"
                f"  hermes gateway run",
                "Health Check",
            )
        return False


async def finalize_setup(
    config: Dict[str, Any],
    settings: Any,
    workspace_dir: str,
    prompter: Optional[WizardPrompter] = None,
) -> FinalizeResult:
    """Finalize the setup wizard.

    Displays summary, runs health check, and suggests next steps.

    Adapted from finalizeSetupWizard() in setup.finalize.ts.
    """
    if prompter is None:
        from wizard_prompts import TerminalPrompter
        prompter = TerminalPrompter()

    result = FinalizeResult()

    # ── Summary ────────────────────────────────────────────────────────
    gw_config = config.get("gateway", {})
    port = gw_config.get("port", 18789)
    bind = gw_config.get("bind", "loopback")
    auth_mode = gw_config.get("auth", {}).get("mode", "token")

    urls = {
        "ws": f"ws://127.0.0.1:{port}",
        "http": f"http://127.0.0.1:{port}",
    }
    result.urls = urls

    summary_lines = [
        "═" * 40,
        "  Hermes Setup Complete",
        "═" * 40,
        f"  Workspace: {workspace_dir}",
        f"  Gateway:   {bind}:{port}",
        f"  Auth:      {auth_mode}",
        f"  URL:       {urls['http']}",
        "",
        "Next steps:",
        "  1. Start the gateway:  hermes gateway run",
        "  2. Connect a platform: hermes configure --platform telegram",
        "  3. Open the TUI:      hermes --tui",
        "",
        "Docs: https://docs.hermes-agent.nousresearch.com",
    ]

    token = gw_config.get("auth", {}).get("token")
    if token:
        masked = "*" * (len(token) - 6) + token[-6:] if len(token) > 6 else "*" * len(token)
        summary_lines.insert(6, f"  Token:     {masked}")

    await prompter.note("\n".join(summary_lines), "Setup Complete")

    # ── Health check ─────────────────────────────────────────────────
    result.gateway_reachable = await run_health_check(
        urls["http"],
        token=token,
        prompter=prompter,
    )
    result.health_ok = result.gateway_reachable

    # ── Next steps ──────────────────────────────────────────────────
    if result.gateway_reachable:
        await prompter.outro("Gateway is running! Open http://127.0.0.1:" + str(port))
    else:
        await prompter.note(
            "Gateway is not running yet.\n"
            "Start it with: hermes gateway run",
            "Next Step",
        )

    return result
