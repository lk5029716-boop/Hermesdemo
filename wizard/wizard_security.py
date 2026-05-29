"""
wizard_security.py — Security disclaimer for setup wizard.

Adapted from OpenClaw src/wizard/setup.security-note.ts.

Displays security warnings during onboarding. Hermes has security_advisories.py
but lacks the interactive wizard security disclaimer flow.
"""

from __future__ import annotations


def get_security_note_title() -> str:
    return "Security disclaimer"


def get_security_confirm_message() -> str:
    return (
        "I understand this is personal-by-default and shared/multi-user "
        "use requires lock-down. Continue?"
    )


def get_security_note_message() -> str:
    """Full security disclaimer text shown during setup."""
    return """
OpenClaw is a hobby project and still in beta. Expect sharp edges.

By default, OpenClaw is a personal agent: one trusted operator boundary.
This bot can read files and run actions if tools are enabled.
A bad prompt can trick it into doing unsafe things.

OpenClaw is not a hostile multi-tenant boundary by default.
If multiple users can message one tool-enabled agent, they share that delegated tool authority.

If you're not comfortable with security hardening and access control, don't run OpenClaw.
Ask someone experienced to help before enabling tools or exposing it to the internet.

Recommended baseline:
- Pairing/allowlists + mention gating.
- Multi-user/shared inbox: split trust boundaries (separate gateway/credentials, ideally separate OS users/hosts).
- Sandbox + least-privilege tools.
- Shared inboxes: isolate DM sessions (session.dmScope: per-channel-peer) and keep tool access minimal.
- Keep secrets out of the agent's reachable filesystem.
- Use the strongest available model for any bot with tools or untrusted inboxes.

Run regularly:
  openclaw security audit --deep
  openclaw security audit --fix

Learn more:
  https://docs.openclaw.ai/gateway/security
""".strip()
