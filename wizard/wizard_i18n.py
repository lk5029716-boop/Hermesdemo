"""
wizard_i18n.py — Wizard internationalization and translations.

Adapted from OpenClaw src/wizard/i18n/ (index.ts, types.ts, locales/en.ts).

Hermes has agent/i18n.py but lacks wizard-specific translation keys
for setup flow, gateway config, plugin setup, migration, security notes.
"""

from __future__ import annotations

import os
from typing import Optional

# Supported locales
WIZARD_DEFAULT_LOCALE = "en"
WIZARD_SUPPORTED_LOCALES = ["en", "zh-CN", "zh-TW"]

# Translation map — English (default)
EN = {
    "common": {
        "back": "Back",
        "done": "Done",
        "docs": "Docs:",
        "finished": "Finished",
        "noAuth": "No auth",
        "password": "Password",
        "required": "Required",
        "minute": "{count} minute",
        "minutes": "{count} minutes",
        "second": "{count} second",
        "seconds": "{count} seconds",
        "skip": "Skip",
        "skipForNow": "Skip for now",
        "tokenRecommended": "Token (recommended)",
    },
    "wizard": {
        "gateway": {
            "accessProtection": "Gateway access protection",
            "auth": "Gateway auth",
            "bindAddress": "Gateway bind address",
            "bindAuto": "Auto (Loopback -> LAN)",
            "bindCustom": "Custom IP",
            "bindLan": "LAN (0.0.0.0)",
            "bindLoopback": "Loopback (127.0.0.1)",
            "bindTailnet": "Tailnet (Tailscale IP)",
            "port": "Gateway port",
            "tokenPrompt": "Gateway token",
            "websocketUrl": "Gateway WebSocket URL",
        },
        "setup": {
            "intro": "OpenClaw setup",
            "flowQuickstart": "QuickStart (recommended)",
            "flowAdvanced": "Manual setup",
            "quickstartTitle": "QuickStart",
            "setupMode": "Setup mode",
            "configHandling": "Config handling",
            "keepCurrent": "Keep current values",
            "modifyCurrent": "Review and update",
            "resetBefore": "Reset before setup",
            "resetScope": "Reset scope",
            "resetConfig": "Config only",
            "resetConfigCredsSessions": "Config + creds + sessions",
            "resetFull": "Full reset (config + creds + sessions + workspace)",
            "existingConfigTitle": "Existing config detected",
            "invalidConfigTitle": "Invalid config",
            "workspaceDirectory": "Workspace directory",
            "channelsTitle": "Channels",
            "skillsTitle": "Skills",
            "riskNotAccepted": "risk not accepted",
            "secretRefProbeFailed": "Could not resolve {field} SecretRef for setup probe.",
        },
        "completion": {
            "enable": "Enable {shell} shell completion for {cli}?",
            "installed": "Shell completion installed. {reloadHint}",
            "title": "Shell completion",
            "cacheFailed": "Failed to generate completion cache. Run `{command}` later.",
            "reloadShell": "Restart your shell or run: source {profile}",
            "reloadPowerShell": "Restart your shell or run: {command}",
        },
        "migration": {
            "apply": "Apply this migration now?",
            "appliedTitle": "Migration applied",
            "cancelled": "migration cancelled",
            "complete": "Migration complete. Run `openclaw doctor` next.",
            "previewTitle": "Migration preview",
            "source": "Migration source",
            "sourceAgentHome": "Source agent home",
            "sourcePathHint": "Enter a source path next",
            "targetWorkspace": "Target workspace directory",
        },
        "plugins": {
            "configureSelect": "Select plugin to configure",
            "configureSelectOnboard": "Configure plugins (select to set up now, or skip)",
            "configureFieldsTitle": "Plugin setup",
            "configurePlugin": "Configure {plugin}",
            "configureEmpty": "No plugins with configurable fields found.",
            "configureEmptyTitle": "Plugins",
            "configureBackHint": "Return to section menu",
            "configuredCount": "{configured}/{total} configured",
            "currentValue": "Keep current ({value})",
            "fieldsCount": "{count} field{plural}",
            "installTitle": "Plugin install",
            "officialInstall": "Install optional plugins",
            "officialSkipHint": "Continue without installing optional plugins",
            "sensitiveField": '"{label}" is sensitive. Set it via config or Web UI.',
            "sensitiveTitle": "Sensitive field",
            "skipConfigHint": "Continue without configuring plugins",
            "arrayPromptSuffix": " (comma-separated, empty to clear)",
            "arrayPlaceholder": "value1, value2",
        },
        "security": {
            "title": "Security disclaimer",
            "confirm": "I understand this is personal-by-default and shared/multi-user use requires lock-down. Continue?",
            "beta": "OpenClaw is a hobby project and still in beta. Expect sharp edges.",
            "personalAgent": "By default, OpenClaw is a personal agent: one trusted operator boundary.",
            "toolAccess": "This bot can read files and run actions if tools are enabled.",
            "promptRisk": "A bad prompt can trick it into doing unsafe things.",
            "notMultitenant": "OpenClaw is not a hostile multi-tenant boundary by default.",
            "sharedAuthority": "If multiple users can message one tool-enabled agent, they share that delegated tool authority.",
            "hardeningRequired": "If you're not comfortable with security hardening and access control, don't run OpenClaw.",
            "askForHelp": "Ask someone experienced to help before enabling tools or exposing it to the internet.",
            "recommendedBaseline": "Recommended baseline",
            "baselinePairing": "Pairing/allowlists + mention gating.",
            "baselineSharedInbox": "Multi-user/shared inbox: split trust boundaries.",
            "baselineSandbox": "Sandbox + least-privilege tools.",
            "baselineDmSessions": "Shared inboxes: isolate DM sessions.",
            "baselineSecrets": "Keep secrets out of the agent's reachable filesystem.",
            "baselineStrongModel": "Use the strongest available model for any bot with tools or untrusted inboxes.",
            "runRegularly": "Run regularly",
            "learnMore": "Learn more",
        },
    },
}

LOCALES = {
    "en": EN,
}


class WizardI18n:
    """Wizard translation engine with locale resolution and interpolation."""

    def __init__(self, locale: Optional[str] = None):
        self.locale = self._resolve_locale(locale)

    def _resolve_locale(self, value: Optional[str]) -> str:
        """Resolve a locale string to a supported locale, defaulting to 'en'."""
        normalized = (value or "").strip().split(".")[0].split("@")[0].replace("_", "-")
        if not normalized:
            return WIZARD_DEFAULT_LOCALE
        lower = normalized.lower()
        if lower == "en" or lower.startswith("en-"):
            return "en"
        if lower in ("zh-tw", "zh-hk", "zh-mo") or "hant" in lower:
            return "zh-TW"
        if lower in ("zh", "zh-cn", "zh-sg") or "hans" in lower:
            return "zh-CN"
        return WIZARD_DEFAULT_LOCALE

    @classmethod
    def from_env(cls) -> "WizardI18n":
        """Create a WizardI18n from environment variables."""
        locale = os.environ.get("OPENCLAW_LOCALE") or os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG")
        return cls(locale)

    def t(self, key: str, params: Optional[dict] = None) -> str:
        """Translate a key, falling back to the key itself if not found."""
        result = self._read_key(key)
        if result is None:
            result = key
        if params:
            result = self._interpolate(result, params)
        return result

    def _read_key(self, key: str) -> Optional[str]:
        """Read a dot-separated key from the locale map."""
        locale_map = LOCALES.get(self.locale, LOCALES[WIZARD_DEFAULT_LOCALE])
        parts = key.split(".")
        current: dict = locale_map
        for segment in parts:
            if not isinstance(current, dict) or segment not in current:
                return None
            current = current[segment]  # type: ignore
        return current if isinstance(current, str) else None

    @staticmethod
    def _interpolate(value: str, params: dict) -> str:
        """Replace {key} placeholders with param values."""
        import re
        return re.sub(r"\{([A-Za-z0-9_]+)\}", lambda m: str(params.get(m.group(1), m.group(0))), value)


# Module-level convenience: pre-built translator instance
_default_i18n = WizardI18n.from_env()


def t(key: str, params: Optional[dict] = None) -> str:
    """Translate using the default env-resolved locale."""
    return _default_i18n.t(key, params)
