"""
wizard_setup.py — Main setup wizard flow.

Adapted from OpenClaw src/wizard/setup.ts (runSetupWizard).

This is a NEW feature for Hermes — there was no equivalent before.
OpenClaw's wizard is a full interactive onboarding that:
  1. Shows security risk acknowledgement
  2. Detects existing config and offers keep/modify/reset
  3. Selects flow: quickstart / advanced / import
  4. Configures auth (provider selection, model picker)
  5. Configures gateway (port, bind, auth, tailscale)
  6. Sets up channels (Telegram, Discord, etc.)
  7. Configures search, skills, plugins, hooks
  8. Finalizes: daemon install, health check, control UI, TUI launch

Hermes adaptation:
  - No daemon/systemd (Railway/cloud-native)
  - No tailscale (not applicable)
  - No TUI launch (Hermes uses its own TUI system)
  - Keeps: security ack, config detection, flow selection, gateway config,
    channel setup, plugin config, finalize/health check
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from gateway.wizard_prompts import (
    WizardCancelledError,
    WizardPrompter,
    WizardSelectOption,
)
from gateway.wizard_gateway_config import (
    GatewayWizardSettings,
    QuickstartGatewayDefaults,
    configure_gateway,
)

logger = logging.getLogger(__name__)


# ── Types ──────────────────────────────────────────────────────────────────

WizardFlow = str  # "quickstart" | "advanced" | "import"


@dataclass
class OnboardOptions:
    """Options for the setup wizard.

    Adapted from OnboardOptions in src/commands/onboard-types.ts.
    """
    flow: Optional[str] = None          # "quickstart" | "advanced" | "import"
    mode: Optional[str] = None          # "local" | "remote"
    workspace: Optional[str] = None     # workspace directory
    auth_choice: Optional[str] = None   # provider id or "skip"
    accept_risk: bool = False
    skip_bootstrap: bool = False
    skip_channels: bool = False
    skip_providers: bool = False
    skip_search: bool = False
    skip_skills: bool = False
    skip_hooks: bool = False
    skip_health: bool = False
    skip_ui: bool = False
    non_interactive: bool = False


@dataclass
class WizardResult:
    """Result of running the setup wizard."""
    config: Dict[str, Any] = field(default_factory=dict)
    settings: Optional[GatewayWizardSettings] = None
    flow: str = "quickstart"
    cancelled: bool = False
    error: Optional[str] = None


# ── Security ───────────────────────────────────────────────────────────────

SECURITY_NOTE = """\
⚠️  SECURITY NOTICE

This is a personal AI agent with access to:
  • Your files and filesystem
  • Shell command execution
  • Connected messaging platforms
  • API keys and secrets

Recommended baseline:
  • Use pairing mode for new DM senders
  • Enable sandbox for shell execution
  • Use token-based gateway auth
  • Run regular security audits

Docs: https://docs.hermes-agent.nousresearch.com/security
"""


# ── Config detection ───────────────────────────────────────────────────────

def detect_existing_config() -> Dict[str, Any]:
    """Detect existing Hermes config from ~/.hermes/config.yaml."""
    import os
    from pathlib import Path

    config_path = Path.home() / ".hermes" / "config.yaml"
    if not config_path.exists():
        return {}

    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def detect_quickstart_defaults(config: Dict[str, Any]) -> QuickstartGatewayDefaults:
    """Extract gateway defaults from existing config for quickstart mode."""
    gw = config.get("gateway", {})
    return QuickstartGatewayDefaults(
        has_existing=bool(gw),
        port=gw.get("port", 18789),
        bind=gw.get("bind", "loopback"),
        auth_mode=gw.get("auth", {}).get("mode", "token"),
        token=gw.get("auth", {}).get("token"),
        password=gw.get("auth", {}).get("password"),
        custom_bind_host=gw.get("customBindHost"),
    )


# ── Main wizard ────────────────────────────────────────────────────────────

async def run_setup_wizard(
    opts: Optional[OnboardOptions] = None,
    prompter: Optional[WizardPrompter] = None,
) -> WizardResult:
    """Run the Hermes setup wizard.

    This is the main entry point, adapted from runSetupWizard() in setup.ts.

    Flow:
      1. Security risk acknowledgement
      2. Detect existing config → keep / modify / reset
      3. Select flow: quickstart / advanced
      4. Configure gateway (port, bind, auth)
      5. Set up channels
      6. Configure plugins
      7. Finalize (health check, summary)
    """
    if opts is None:
        opts = OnboardOptions()
    if prompter is None:
        from gateway.wizard_prompts import TerminalPrompter
        prompter = TerminalPrompter()

    result = WizardResult()

    try:
        # ── Step 1: Intro + Security ─────────────────────────────────
        await prompter.intro("Hermes Setup Wizard")
        await prompter.note(
            "Welcome! This wizard will guide you through setting up Hermes.",
            "Welcome",
        )

        if not opts.accept_risk:
            await prompter.note(SECURITY_NOTE, "Security Notice")
            accepted = await prompter.confirm(
                message="I understand the security implications. Continue?",
                initial_value=False,
            )
            if not accepted:
                raise WizardCancelledError("Security risk not accepted")

        # ── Step 2: Detect existing config ──────────────────────────
        existing_config = detect_existing_config()
        base_config: Dict[str, Any] = existing_config.copy()

        if existing_config:
            await prompter.note(
                f"Existing config detected at ~/.hermes/config.yaml\n"
                f"  Platforms: {list(existing_config.get('platforms', {}).keys())}\n"
                f"  Gateway port: {existing_config.get('gateway', {}).get('port', 'not set')}",
                "Existing Config",
            )
            action = await prompter.select(
                message="How to handle existing config?",
                options=[
                    WizardSelectOption("keep", "Keep current settings"),
                    WizardSelectOption("modify", "Modify settings"),
                    WizardSelectOption("reset", "Reset and start fresh"),
                ],
                initial_value="keep",
            )
            if action == "reset":
                base_config = {}
                await prompter.note("Config reset. Starting fresh.", "Reset")

        # ── Step 3: Select flow ─────────────────────────────────────
        explicit_flow = opts.flow
        if explicit_flow in ("quickstart", "advanced", "import"):
            flow: WizardFlow = explicit_flow
        else:
            flow = await prompter.select(
                message="Setup mode?",
                options=[
                    WizardSelectOption(
                        "quickstart",
                        "Quick Start",
                        "Recommended — minimal prompts, smart defaults",
                    ),
                    WizardSelectOption(
                        "advanced",
                        "Advanced",
                        "Full control over every setting",
                    ),
                ],
                initial_value="quickstart",
            )

        if flow == "import":
            await prompter.note(
                "Migration import: use `hermes migrate <provider>` to import from another agent.",
                "Import",
            )
            result.flow = "import"
            result.config = base_config
            return result

        result.flow = flow

        # ── Step 4: Workspace ───────────────────────────────────────
        import os
        default_workspace = os.path.expanduser("~/.hermes/workspace")
        if flow == "quickstart":
            workspace = base_config.get("workspace", default_workspace)
        else:
            workspace = await prompter.text(
                message="Workspace directory?",
                initial_value=base_config.get("workspace", default_workspace),
            )

        # ── Step 5: Auth choice ─────────────────────────────────────
        if opts.auth_choice and opts.auth_choice != "skip":
            auth_choice = opts.auth_choice
        elif flow == "quickstart":
            auth_choice = "openrouter"  # sensible default
        else:
            auth_choice = await prompter.select(
                message="AI provider?",
                options=[
                    WizardSelectOption("openrouter", "OpenRouter (recommended)"),
                    WizardSelectOption("anthropic", "Anthropic (Claude)"),
                    WizardSelectOption("openai", "OpenAI (GPT)"),
                    WizardSelectOption("custom-api-key", "Custom API key"),
                    WizardSelectOption("skip", "Skip for now"),
                ],
                initial_value="openrouter",
            )

        if auth_choice and auth_choice != "skip":
            base_config["provider"] = auth_choice
            await prompter.note(f"Provider set to: {auth_choice}", "Auth")

        # ── Step 6: Gateway configuration ───────────────────────────
        quickstart_defaults = detect_quickstart_defaults(base_config)
        gw_config, gw_settings = await configure_gateway(
            flow=flow,
            existing_config=base_config.get("gateway", {}),
            prompter=prompter,
        )
        base_config["gateway"] = gw_config
        result.settings = gw_settings

        # ── Step 7: Channels ────────────────────────────────────────
        if not opts.skip_channels:
            await prompter.note(
                "Channel setup: Configure which messaging platforms to connect.\n"
                "You can also do this later with `hermes configure`.",
                "Channels",
            )
            # In a full implementation this would list available channel plugins
            # and prompt for each. For now we note it.
            configured_platforms = list(base_config.get("platforms", {}).keys())
            if configured_platforms:
                await prompter.note(
                    f"Already configured: {', '.join(configured_platforms)}",
                    "Channels",
                )

        # ── Step 8: Plugins ─────────────────────────────────────────
        if not opts.skip_channels and flow == "advanced":
            await prompter.note(
                "Plugin configuration: Additional plugins can be installed.\n"
                "Use `hermes plugins` to manage plugins later.",
                "Plugins",
            )

        # ── Step 9: Finalize ────────────────────────────────────────
        await prompter.note(
            f"Setup complete!\n"
            f"  Flow: {flow}\n"
            f"  Workspace: {workspace}\n"
            f"  Gateway: {gw_config.get('bind', 'loopback')}:{gw_config.get('port', 18789)}\n"
            f"  Auth: {gw_config.get('auth', {}).get('mode', 'token')}",
            "Summary",
        )

        # Health check (if gateway is running)
        if not opts.skip_health:
            await prompter.note(
                "Run `hermes gateway health` to verify the gateway is reachable.",
                "Health Check",
            )

        await prompter.outro("Hermes is ready! 🎉")
        result.config = base_config

    except WizardCancelledError:
        result.cancelled = True
        await prompter.outro("Setup cancelled.")
    except Exception as exc:
        result.error = str(exc)
        logger.exception("Setup wizard failed")
        await prompter.note(f"Error: {exc}", "Error")

    return result


# ── CLI entry point ────────────────────────────────────────────────────────

def main():
    """CLI entry point for the setup wizard."""
    import asyncio
    asyncio.run(run_setup_wizard())


if __name__ == "__main__":
    main()
