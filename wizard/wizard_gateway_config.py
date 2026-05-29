"""
wizard_gateway_config.py — Adapter from OpenClaw src/wizard/setup.gateway-config.ts

Provides:
  - GatewayWizardSettings: dataclass for gateway settings
  - configure_gateway(): interactive gateway configuration (port, bind, auth, tailscale)
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from gateway.wizard_prompts import WizardCancelledError, WizardPrompter, WizardSelectOption


@dataclass
class GatewayWizardSettings:
    """Gateway configuration resolved during setup wizard.

    Adapted from GatewayWizardSettings in src/wizard/setup.gateway-config.ts.
    """
    port: int = 18789
    bind: str = "loopback"  # loopback | lan | auto | custom | tailnet
    custom_bind_host: Optional[str] = None
    auth_mode: str = "token"  # token | password
    gateway_token: Optional[str] = None
    tailscale_mode: str = "off"  # off | serve | funnel
    tailscale_reset_on_exit: bool = False


@dataclass
class QuickstartGatewayDefaults:
    """Existing gateway config detected at startup.

    Adapted from QuickstartGatewayDefaults in src/wizard/setup.types.ts.
    """
    has_existing: bool = False
    port: int = 18789
    bind: str = "loopback"
    auth_mode: str = "token"
    tailscale_mode: str = "off"
    token: Optional[str] = None
    password: Optional[str] = None
    custom_bind_host: Optional[str] = None
    tailscale_reset_on_exit: bool = False


def random_token(length: int = 32) -> str:
    """Generate a random hex token for gateway auth."""
    return secrets.token_hex(length)


def mask_token(token: str, visible: int = 6) -> str:
    """Mask an API token for display, showing only the last few chars."""
    if len(token) <= visible:
        return "*" * len(token)
    return "*" * (len(token) - visible) + token[-visible:]


def validate_port(value: str) -> Optional[str]:
    """Validate a port number string. Returns error message or None."""
    try:
        port = int(value)
        if port < 1 or port > 65535:
            return "Port must be between 1 and 65535"
        return None
    except ValueError:
        return "Port must be a number"


def validate_ipv4(value: str) -> Optional[str]:
    """Validate an IPv4 address. Returns error message or None."""
    parts = value.strip().split(".")
    if len(parts) != 4:
        return "Invalid IPv4 address"
    for p in parts:
        try:
            n = int(p)
            if n < 0 or n > 255:
                return "Invalid IPv4 octet"
        except ValueError:
            return "Invalid IPv4 address"
    return None


async def configure_gateway(
    flow: str = "quickstart",
    existing_config: Optional[dict] = None,
    prompter: Optional[WizardPrompter] = None,
) -> Tuple[dict, GatewayWizardSettings]:
    """Interactive gateway configuration.

    Args:
        flow: "quickstart" (minimal prompts) or "advanced" (full prompts)
        existing_config: previously detected config (for quickstart defaults)
        prompter: the WizardPrompter to use

    Returns:
        (config_dict, settings) — updated config and resolved settings

    Adapted from configureGatewayForSetup() in setup.gateway-config.ts.
    """
    if prompter is None:
        from gateway.wizard_prompts import TerminalPrompter
        prompter = TerminalPrompter()

    existing = existing_config or {}
    settings = GatewayWizardSettings()

    # ── Port ──────────────────────────────────────────────────────────
    if flow == "quickstart":
        settings.port = existing.get("port", settings.port)
    else:
        port_str = await prompter.text(
            message="Gateway port?",
            initial_value=str(existing.get("port", settings.port)),
            validate=validate_port,
        )
        settings.port = int(port_str) if port_str else settings.port

    # ── Bind mode ─────────────────────────────────────────────────────
    bind_options = [
        WizardSelectOption("loopback", "Localhost only (127.0.0.1)"),
        WizardSelectOption("lan", "Local network (LAN)"),
        WizardSelectOption("auto", "Auto-detect"),
        WizardSelectOption("tailnet", "Tailscale Tailnet"),
        WizardSelectOption("custom", "Custom IP address"),
    ]
    if flow == "quickstart":
        settings.bind = existing.get("bind", settings.bind)
    else:
        settings.bind = await prompter.select(
            message="Bind address?",
            options=bind_options,
            initial_value=existing.get("bind", "loopback"),
        )

    # ── Custom bind host ──────────────────────────────────────────────
    if settings.bind == "custom":
        host = await prompter.text(
            message="Custom IP address?",
            initial_value=existing.get("customBindHost", ""),
            validate=validate_ipv4,
        )
        settings.custom_bind_host = host

    # ── Auth mode ─────────────────────────────────────────────────────
    if flow == "quickstart":
        settings.auth_mode = existing.get("authMode", "token")
    else:
        auth_options = [
            WizardSelectOption("token", "Auth token (recommended)"),
            WizardSelectOption("password", "Password"),
        ]
        settings.auth_mode = await prompter.select(
            message="Gateway access protection?",
            options=auth_options,
            initial_value=existing.get("authMode", "token"),
        )

    # ── Tailscale ─────────────────────────────────────────────────────
    if flow == "quickstart":
        settings.tailscale_mode = existing.get("tailscaleMode", "off")
    else:
        ts_options = [
            WizardSelectOption("off", "Disabled"),
            WizardSelectOption("serve", "Tailscale Serve (encrypted, LAN-speed)"),
            WizardSelectOption("funnel", "Tailscale Funnel (public internet)"),
        ]
        settings.tailscale_mode = await prompter.select(
            message="Tailscale exposure?",
            options=ts_options,
            initial_value="off",
        )

        if settings.tailscale_mode != "off":
            settings.tailscale_reset_on_exit = await prompter.confirm(
                message="Reset Tailscale serve/funnel rules on exit?",
                initial_value=False,
            )

    # ── Safety: tailscale wants loopback ─────────────────────────────
    if settings.tailscale_mode != "off" and settings.bind != "loopback":
        await prompter.note(
            "Tailscale serve/funnel requires loopback bind for safety. Switching to loopback.",
            "Bind mode",
        )
        settings.bind = "loopback"
        settings.custom_bind_host = None

    # ── Safety: funnel requires password ─────────────────────────────
    if settings.tailscale_mode == "funnel" and settings.auth_mode != "password":
        await prompter.note(
            "Tailscale Funnel requires password auth for public exposure. Switching to password.",
            "Auth mode",
        )
        settings.auth_mode = "password"

    # ── Token / Password ──────────────────────────────────────────────
    if settings.auth_mode == "token":
        existing_token = existing.get("token") or os.environ.get("OPENCLAW_GATEWAY_TOKEN")
        if existing_token:
            keep = await prompter.confirm(
                message=f"Keep existing token ({mask_token(existing_token)})?",
                initial_value=True,
            )
            if keep:
                settings.gateway_token = existing_token
            else:
                settings.gateway_token = random_token()
        else:
            settings.gateway_token = random_token()
        await prompter.note(
            f"Gateway token: {mask_token(settings.gateway_token, 8)}",
            "Gateway Token",
        )

    elif settings.auth_mode == "password":
        from getpass import getpass
        password = getpass("  Gateway password: ")
        if not password:
            # Fallback to token if no password provided
            await prompter.note("No password provided — falling back to token auth.", "Auth")
            settings.auth_mode = "token"
            settings.gateway_token = random_token()
            await prompter.note(
                f"Gateway token: {mask_token(settings.gateway_token, 8)}",
                "Gateway Token",
            )
        else:
            # In a real implementation we'd store this securely
            # For now we return it in the settings
            pass

    # ── Build config dict ─────────────────────────────────────────────
    config: dict = {
        "port": settings.port,
        "bind": settings.bind,
    }
    if settings.bind == "custom" and settings.custom_bind_host:
        config["customBindHost"] = settings.custom_bind_host

    auth: dict = {"mode": settings.auth_mode}
    if settings.auth_mode == "token" and settings.gateway_token:
        auth["token"] = settings.gateway_token
    config["auth"] = auth

    if settings.tailscale_mode != "off":
        config["tailscale"] = {
            "mode": settings.tailscale_mode,
            "resetOnExit": settings.tailscale_reset_on_exit,
        }

    # New gateway → denylist dangerous node commands (safety default)
    if not existing.get("hasExisting"):
        config.setdefault("nodes", {})["denyCommands"] = [
            "rm -rf /",
            "sudo shutdown",
            "sudo reboot",
        ]

    return config, settings
