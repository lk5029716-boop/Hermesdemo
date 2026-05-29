"""Status text utilities.

Ported from OpenClaw src/status/

Only the portable, standalone utilities are included.
Most of this folder is deeply tied to OpenClaw's config, agent, and terminal systems.
"""

from .labels import format_fast_mode_label

__all__ = ["format_fast_mode_label"]
