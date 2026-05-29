"""
wizard/__init__.py — Setup wizard system.

Adapted from OpenClaw src/wizard/.

Provides a modular setup wizard with:
- Step-by-step session with deferred answers (wizard_session.py)
- Terminal prompter with searchable select/multiselect (wizard_clack.py, wizard_prompts.py)
- Shell completion installation (wizard_completion.py)
- Security disclaimer (wizard_security.py)
- Plugin installation from official catalog (wizard_plugins.py)
- Plugin field configuration via uiHints (wizard_plugin_config.py)
- Migration import from other agents (wizard_migration.py)
- Post-install migration offers (wizard_post_install.py)
- SecretRef resolution (wizard_secret.py)
- Internationalization (wizard_i18n.py)
- Wizard flow types (wizard_types.py)
"""

from .wizard_prompts import (
    WizardCancelledError,
    WizardPrompter,
    WizardProgress,
    WizardSelectOption,
    TerminalPrompter,
    TerminalProgress,
)
from .wizard_session import WizardSession, WizardStep, WizardNextResult
from .wizard_types import (
    WizardFlow,
    GatewayBind,
    GatewayAuthChoice,
    TailscaleMode,
    QuickstartGatewayDefaults,
    GatewayWizardSettings,
    SecretRef,
)
from .wizard_security import (
    get_security_note_title,
    get_security_confirm_message,
    get_security_note_message,
)
from .wizard_i18n import WizardI18n, t

__all__ = [
    "WizardCancelledError",
    "WizardPrompter",
    "WizardProgress",
    "WizardSelectOption",
    "TerminalPrompter",
    "TerminalProgress",
    "WizardSession",
    "WizardStep",
    "WizardNextResult",
    "WizardFlow",
    "GatewayBind",
    "GatewayAuthChoice",
    "TailscaleMode",
    "QuickstartGatewayDefaults",
    "GatewayWizardSettings",
    "SecretRef",
    "get_security_note_title",
    "get_security_confirm_message",
    "get_security_note_message",
    "WizardI18n",
    "t",
]
