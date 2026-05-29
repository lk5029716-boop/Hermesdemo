"""
wizard_types.py — Wizard flow types and gateway settings.

Adapted from OpenClaw src/wizard/setup.types.py.

Defines types for wizard flow selection, gateway auth choices,
and quickstart defaults. Hermes setup.py has partial equivalents
but lacks the structured gateway wizard settings types.
"""

from __future__ import annotations

from typing import Literal, Optional, Union

# Flow selection: quickstart wizard vs advanced manual setup
WizardFlow = Literal["quickstart", "advanced"]

# Gateway bind modes
GatewayBind = Literal["loopback", "lan", "auto", "custom", "tailnet"]

# Gateway auth modes
GatewayAuthChoice = Literal["token", "password"]

# Tailscale exposure modes
TailscaleMode = Literal["off", "serve", "unnel"]

# Secret input value — plaintext string or SecretRef dict
SecretInput = Union[str, "SecretRef"]


class SecretRef:
    """Reference to a secret stored outside plaintext config."""
    def __init__(self, source: str, provider: str, id: str):
        self.source = source
        self.provider = provider
        self.id = id


class QuickstartGatewayDefaults:
    """Default gateway settings detected from existing config for quickstart flow."""
    def __init__(
        self,
        has_existing: bool,
        port: int,
        bind: GatewayBind,
        auth_mode: GatewayAuthChoice,
        tailscale_mode: TailscaleMode,
        token: Optional[SecretInput] = None,
        password: Optional[SecretInput] = None,
        custom_bind_host: Optional[str] = None,
        tailscale_reset_on_exit: bool = False,
    ):
        self.has_existing = has_existing
        self.port = port
        self.bind = bind
        self.auth_mode = auth_mode
        self.tailscale_mode = tailscale_mode
        self.token = token
        self.password = password
        self.custom_bind_host = custom_bind_host
        self.tailscale_reset_on_exit = tailscale_reset_on_exit


class GatewayWizardSettings:
    """Gateway settings configured via the wizard."""
    def __init__(
        self,
        port: int,
        bind: GatewayBind,
        auth_mode: GatewayAuthChoice,
        gateway_token: Optional[str] = None,
        tailscale_mode: TailscaleMode = "off",
        tailscale_reset_on_exit: bool = False,
        custom_bind_host: Optional[str] = None,
    ):
        self.port = port
        self.bind = bind
        self.auth_mode = auth_mode
        self.gateway_token = gateway_token
        self.tailscale_mode = tailscale_mode
        self.tailscale_reset_on_exit = tailscale_reset_on_exit
        self.custom_bind_host = custom_bind_host
