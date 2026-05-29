"""
wizard_setup.py — Main setup wizard orchestrator.

Adapted from OpenClaw src/wizard/setup.ts (runSetupWizard, 874 lines)
+ setup.completion.ts + setup.gateway-config.ts + setup.finalize.ts.

Full orchestrator that calls all submodules in sequence:
  1. Security risk acknowledgement
  2. Config snapshot validation + keep/modify/reset
  3. Flow selection: quickstart / advanced / import
  4. Auth provider + model selection
  5. Gateway config (port, bind, tailscale, token/password)
  6. Channel setup
  7. Search, skills, plugins, hooks
  8. Shell completion install
  9. Finalize: health check, summary, workspace init
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from wizard_prompts import (
    WizardCancelledError,
    WizardPrompter,
    WizardSelectOption,
)
from wizard_gateway_config import (
    GatewayWizardSettings,
    QuickstartGatewayDefaults,
    configure_gateway,
)

logger = logging.getLogger(__name__)

WizardFlow = str  # "quickstart" | "advanced"


@dataclass
class OnboardOptions:
    """Options for the setup wizard."""
    flow: Optional[str] = None
    mode: Optional[str] = None
    workspace: Optional[str] = None
    auth_choice: Optional[str] = None
    accept_risk: bool = False
    skip_bootstrap: bool = False
    skip_channels: bool = False
    skip_providers: bool = False
    skip_search: bool = False
    skip_skills: bool = False
    skip_hooks: bool = False
    skip_health: bool = False
    skip_ui: bool = False
    skip_completion: bool = False
    import_from: Optional[str] = None
    non_interactive: bool = False


@dataclass
class WizardResult:
    """Result of running the setup wizard."""
    config: Dict[str, Any] = field(default_factory=dict)
    settings: Optional[GatewayWizardSettings] = None
    flow: str = "quickstart"
    cancelled: bool = False
    error: Optional[str] = None


# ── Security ────────────────────────────────────────────────────────────────

SECURITY_NOTE = """\
⚠️  SECURITY NOTICE

This agent has access to:
  • Your files and filesystem
  • Shell command execution
  • Connected messaging platforms
  • API keys and secrets

Recommended baseline:
  • Use token-based gateway auth
  • Enable sandbox for untrusted sessions
  • Use pairing/allowlists for DMs
  • Run regular security audits: hermes doctor
  • Keep secrets out of the agent's reachable filesystem

Docs: https://hermes-agent.nousresearch.com/docs/security
"""


async def require_risk_acknowledgement(opts: OnboardOptions, prompter: WizardPrompter) -> None:
    if opts.accept_risk:
        return
    await prompter.note(SECURITY_NOTE, "Security Notice")
    accepted = await prompter.confirm(
        message="I understand the security implications. Continue?",
        initial_value=False,
    )
    if not accepted:
        raise WizardCancelledError("Security risk not accepted")


# ── Config detection ────────────────────────────────────────────────────────

def detect_existing_config() -> Dict[str, Any]:
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
    gw = config.get("gateway", {})
    auth = gw.get("auth", {}) if isinstance(gw, dict) else {}
    return QuickstartGatewayDefaults(
        has_existing=bool(gw),
        port=gw.get("port", 18789) if isinstance(gw, dict) else 18789,
        bind=gw.get("bind", "loopback") if isinstance(gw, dict) else "loopback",
        auth_mode=auth.get("mode", "token") if isinstance(auth, dict) else "token",
        tailscale_mode="off",
        token=auth.get("token") if isinstance(auth, dict) else None,
        password=auth.get("password") if isinstance(auth, dict) else None,
        custom_bind_host=gw.get("customBindHost") if isinstance(gw, dict) else None,
    )


def validate_config_snapshot(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    issues = []
    if not config.get("model") and not config.get("provider"):
        issues.append("No model/provider configured")
    gw = config.get("gateway", {})
    if isinstance(gw, dict):
        port = gw.get("port")
        if port is not None and (not isinstance(port, int) or port < 1 or port > 65535):
            issues.append(f"Invalid gateway port: {port}")
    return len(issues) == 0, issues


def summarize_existing_config(config: Dict[str, Any]) -> str:
    lines = ["Existing config:"]
    if "provider" in config:
        lines.append(f"  Provider: {config['provider']}")
    if "model" in config:
        model = config["model"]
        lines.append(f"  Model: {model.get('default', model) if isinstance(model, dict) else model}")
    gw = config.get("gateway", {})
    if isinstance(gw, dict):
        lines.append(f"  Port: {gw.get('port', 'not set')}")
        lines.append(f"  Bind: {gw.get('bind', 'not set')}")
    platforms = config.get("platforms", {})
    if isinstance(platforms, dict) and platforms:
        lines.append(f"  Platforms: {', '.join(platforms.keys())}")
    return "\n".join(lines)


# ── Auth + Model ────────────────────────────────────────────────────────────

async def prompt_auth_choice(
    flow: str,
    config: Dict[str, Any],
    prompter: WizardPrompter,
) -> tuple[str, Dict[str, Any]]:
    if flow == "quickstart":
        return "openrouter", config

    choice = await prompter.select(
        message="AI provider?",
        options=[
            WizardSelectOption("openrouter", "OpenRouter (recommended)", "Multi-model gateway"),
            WizardSelectOption("anthropic", "Anthropic (Claude)", "Claude Opus/Sonnet/Haiku"),
            WizardSelectOption("openai", "OpenAI (GPT)", "GPT-4o, GPT-4.1, o1, o3"),
            WizardSelectOption("gemini", "Google Gemini", "Gemini 2.5 Pro/Flash"),
            WizardSelectOption("custom-api-key", "Custom API key", "Any OpenAI-compatible endpoint"),
            WizardSelectOption("skip", "Skip for now", "Configure later"),
        ],
        initial_value="openrouter",
    )
    return choice, config


# ── Main wizard ──────────────────────────────────────────────────────────────

async def run_setup_wizard(
    opts: Optional[OnboardOptions] = None,
    prompter: Optional[WizardPrompter] = None,
) -> WizardResult:
    if opts is None:
        opts = OnboardOptions()
    if prompter is None:
        from wizard_prompts import TerminalPrompter
        prompter = TerminalPrompter()

    result = WizardResult()

    try:
        # ── Step 1: Intro + Security ───────────────────────────────────
        await prompter.intro("Hermes Setup Wizard")
        await prompter.note(
            "Welcome! This wizard will guide you through setting up Hermes.\n"
            "You can press Ctrl+C at any time to cancel.",
            "Welcome",
        )
        await require_risk_acknowledgement(opts, prompter)

        # ── Step 2: Detect existing config ────────────────────────────
        existing_config = detect_existing_config()
        base_config: Dict[str, Any] = dict(existing_config) if existing_config else {}
        config_valid, config_issues = validate_config_snapshot(base_config)

        if existing_config and not config_valid:
            await prompter.note(summarize_existing_config(base_config), "Invalid Config")
            for issue in config_issues:
                await prompter.note(f"  - {issue}", "Config Issues")
            await prompter.outro("Config invalid. Run `hermes doctor` to repair, then re-run setup.")
            result.config = base_config
            result.error = "Config invalid"
            return result

        configured_plugins = list(base_config.get("plugins", {}).keys()) if isinstance(base_config.get("plugins"), dict) else []
        if configured_plugins:
            await prompter.note(f"Configured plugins: {', '.join(configured_plugins)}", "Plugin Status")

        # ── Step 3: Existing config → keep/modify/reset ────────────────
        if existing_config:
            await prompter.note(summarize_existing_config(base_config), "Existing Config Detected")
            action = await prompter.select(
                message="How to handle existing config?",
                options=[
                    WizardSelectOption("keep", "Keep current settings", "Preserve all existing config"),
                    WizardSelectOption("modify", "Review and update", "Change specific settings"),
                    WizardSelectOption("reset", "Reset and start fresh", "Clear everything and start over"),
                ],
                initial_value="keep",
            )
            if action == "reset":
                base_config = {}
                await prompter.note("Config reset. Starting fresh.", "Reset")

        # ── Step 4: Flow selection ──────────────────────────────────────
        explicit_flow = opts.flow
        if explicit_flow in ("quickstart", "advanced", "import"):
            flow_val: str = explicit_flow
        else:
            flow_val = await prompter.select(
                message="Setup mode?",
                options=[
                    WizardSelectOption(
                        "quickstart", "Quick Start (recommended)",
                        "Minimal prompts, smart defaults. Change details later with `hermes configure`.",
                    ),
                    WizardSelectOption("advanced", "Advanced", "Full control over every setting"),
                ],
                initial_value="quickstart",
            )

        if flow_val == "import":
            await prompter.note(
                "Migration import: Use `hermes migrate <provider>` to import from another agent.",
                "Import",
            )
            result.flow = "import"
            result.config = base_config
            return result

        result.flow = flow_val

        if opts.mode == "remote" and flow_val == "quickstart":
            await prompter.note("QuickStart only supports local gateways. Switching to Advanced.", "QuickStart")
            flow_val = "advanced"

        # ── Step 5: Workspace ──────────────────────────────────────────
        import os
        default_workspace = os.path.expanduser("~/.hermes/workspace")
        agents_cfg = base_config.get("agents", {})
        if isinstance(agents_cfg, dict):
            agents_defaults = agents_cfg.get("defaults", {})
            if isinstance(agents_defaults, dict):
                existing_ws = agents_defaults.get("workspace", default_workspace)
            else:
                existing_ws = default_workspace
        else:
            existing_ws = default_workspace

        if flow_val == "quickstart":
            workspace_dir = existing_ws
        else:
            workspace_dir = await prompter.text(
                message="Workspace directory?",
                initial_value=existing_ws,
            )

        # ── Step 6: Auth provider + model ──────────────────────────────
        auth_configured = bool(opts.auth_choice) and opts.auth_choice != "skip"
        auth_choice: Optional[str] = None

        if opts.non_interactive and not auth_configured:
            pass
        else:
            auth_choice, base_config = await prompt_auth_choice(flow_val, base_config, prompter)

        if auth_choice and auth_choice != "skip":
            base_config["provider"] = auth_choice
            if auth_choice != "custom-api-key":
                await prompter.note(f"Provider: {auth_choice}", "Auth")

        # ── Step 7: Gateway configuration ──────────────────────────────
        quickstart_defaults = detect_quickstart_defaults(base_config)
        gw_dict = base_config.get("gateway", {})
        local_port = gw_dict.get("port", 18789) if isinstance(gw_dict, dict) else 18789

        gw_config, gw_settings = await configure_gateway(
            flow=flow_val,
            existing_config=gw_dict if isinstance(gw_dict, dict) else {},
            prompter=prompter,
        )
        base_config["gateway"] = gw_config
        result.settings = gw_settings

        # ── Step 8: Channels ───────────────────────────────────────────
        if not opts.skip_channels:
            await prompter.note(
                "Channel setup: Configure which messaging platforms to connect.\n"
                "Available: Telegram, Discord, Slack, Signal, WhatsApp, and more.\n"
                "You can also do this later with `hermes configure --platform <name>`.",
                "Channels",
            )
            platforms_dict = base_config.get("platforms", {})
            configured_platforms = list(platforms_dict.keys()) if isinstance(platforms_dict, dict) else []
            if configured_platforms:
                await prompter.note(f"Already configured: {', '.join(configured_platforms)}", "Channels")
            else:
                setup_now = await prompter.confirm(
                    message="Set up a chat channel now?",
                    initial_value=True,
                )
                if setup_now:
                    await prompter.note(
                        "Use: `hermes configure --platform telegram` (or discord, slack, etc.)",
                        "Channels",
                    )

        # ── Step 9: Search ──────────────────────────────────────────────
        if not opts.skip_search:
            await prompter.note(
                "Search: Configure web search providers (Exa, Brave, etc.).\n"
                "Use `hermes configure --search` to set up.",
                "Search",
            )

        # ── Step 10: Skills ────────────────────────────────────────────
        if not opts.skip_skills:
            await prompter.note(
                "Skills: Hermes includes bundled skills for common tasks.\n"
                "Browse and install more from the skills directory.",
                "Skills",
            )

        # ── Step 11: Plugins (advanced only) ───────────────────────────
        if flow_val != "quickstart":
            await prompter.note(
                "Plugins: memory, image-gen, video-gen, browser, and more.\n"
                "Use `hermes plugins list` to browse, `hermes plugins install <name>` to add.",
                "Plugins",
            )

        # ── Step 12: Shell completion ──────────────────────────────────
        if not opts.skip_completion and not opts.non_interactive:
            setup_comp = await prompter.confirm(
                message="Install shell completion for Hermes CLI?",
                initial_value=True,
            )
            if setup_comp:
                try:
                    from wizard_completion import CompletionInstaller
                    installer = CompletionInstaller("hermes")
                    status = installer.check_status()
                    if status.shell != "unknown":
                        installed = installer.install_to_profile(status.shell)
                        if installed:
                            await prompter.note(
                                f"Shell completion installed for {status.shell}. Restart your shell.",
                                "Completion",
                            )
                    else:
                        await prompter.note(
                            "Could not detect shell. Install manually:\n  hermes completion bash >> ~/.bashrc",
                            "Completion",
                        )
                except Exception as e:
                    logger.warning(f"Completion install failed: {e}")

        # ── Step 13: Hooks ─────────────────────────────────────────────
        if not opts.skip_hooks:
            setup_hooks = await prompter.confirm(message="Enable session hooks (memory on /new)?", initial_value=True)
            if setup_hooks:
                if "hooks" not in base_config:
                    base_config["hooks"] = {}
                if isinstance(base_config["hooks"], dict):
                    base_config["hooks"]["sessionMemory"] = True
                await prompter.note("Session hooks enabled.", "Hooks")

        # ── Step 14: Write config ──────────────────────────────────────
        try:
            import yaml
            from pathlib import Path
            config_path = Path.home() / ".hermes" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                yaml.dump(base_config, f, default_flow_style=False, allow_unicode=True)
            await prompter.note(f"Config saved to {config_path}", "Config Saved")
        except Exception as e:
            logger.error(f"Failed to write config: {e}")
            await prompter.note(f"Warning: Could not write config: {e}", "Config")

        # ── Step 15: Finalize ──────────────────────────────────────────
        from wizard_finalize import finalize_setup
        await finalize_setup(
            config=base_config,
            settings=gw_settings,
            workspace_dir=workspace_dir,
            prompter=prompter,
        )

        # ── Step 16: Ensure workspace + bootstrap ─────────────────────
        from pathlib import Path
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)
        agents_md = Path(workspace_dir) / "AGENTS.md"
        if not agents_md.exists():
            agents_md.write_text("# Hermes Agent Workspace\n\n")

        await prompter.outro("Hermes is ready! 🎉")
        result.config = base_config

    except WizardCancelledError:
        result.cancelled = True
        try:
            await prompter.outro("Setup cancelled.")
        except Exception:
            pass
    except Exception as exc:
        result.error = str(exc)
        logger.exception("Setup wizard failed")
        try:
            await prompter.note(f"Error: {exc}", "Error")
        except Exception:
            pass

    return result


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    import asyncio
    asyncio.run(run_setup_wizard())


if __name__ == "__main__":
    main()
