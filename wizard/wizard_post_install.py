"""
wizard_post_install.py — Post-install migration offers.

Adapted from OpenClaw src/wizard/setup.post-install-migration.ts.

After installing plugins during onboarding, offers to migrate data from
systems those plugins own. Hermes has no equivalent feature.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PostInstallMigrationOptions:
    def __init__(
        self,
        config: dict,
        runtime: Any,
        installed_plugin_ids: list[str],
        prompter=None,
        non_interactive: bool = False,
    ):
        self.config = config
        self.runtime = runtime
        self.installed_plugin_ids = installed_plugin_ids
        self.prompter = prompter
        self.non_interactive = non_interactive


class PostInstallMigrationResult:
    def __init__(self, config: dict):
        self.config = config


async def offer_post_install_migrations(
    options: PostInstallMigrationOptions,
) -> PostInstallMigrationResult:
    """
    Offer interactive migration for any migration provider owned by a plugin
    that was just installed during onboarding.

    In non-interactive mode, only emits hint lines.
    """
    if not options.installed_plugin_ids:
        return PostInstallMigrationResult(config=options.config)

    # Resolve migration providers owned by installed plugins
    candidates = await _resolve_candidates(
        config=options.config,
        runtime=options.runtime,
        installed_plugin_ids=options.installed_plugin_ids,
    )

    if not candidates:
        return PostInstallMigrationResult(config=options.config)

    next_config = options.config
    interactive = (
        options.non_interactive is True
        and hasattr(options, "prompter")
        and options.prompter is not None
    )

    for candidate in candidates:
        if not interactive or not options.prompter:
            _log_migration_hint(options.runtime, candidate)
            continue

        description = _describe_candidate(candidate)
        try:
            accepted = options.prompter.confirm(
                message=f"Migrate {description} into this agent now?",
                default=False,
            )
        except Exception:
            logger.info(f"Skipping {candidate['provider'].get('label', '?')} migration prompt")
            _log_migration_hint(options.runtime, candidate)
            continue

        if not accepted:
            _log_migration_hint(options.runtime, candidate)
            continue

        try:
            migration_result = await _run_migration(
                provider=candidate["provider"],
                source=candidate.get("source"),
                config=next_config,
                runtime=options.runtime,
            )
            # Apply config patches from migration result
            next_config = _apply_config_patches(next_config, migration_result)
        except Exception as e:
            label = candidate["provider"].get("label", "?")
            logger.error(f"{label} migration failed: {e}")

    return PostInstallMigrationResult(config=next_config)


async def _resolve_candidates(
    config: dict,
    runtime: Any,
    installed_plugin_ids: list[str],
) -> list[dict]:
    """
    Resolve migration providers owned by newly installed plugins.
    Returns list of {"provider": ..., "source": ...} dicts.
    """
    candidates = []
    installed_ids = set(installed_plugin_ids)

    # This would normally query the plugin registry for migration providers
    # For now, return empty — migration providers register themselves
    try:
        from hermes_cli.plugins import _ensure_plugins_discovered
        _ensure_plugins_discovered()
    except Exception:
        pass

    return candidates


def _describe_candidate(candidate: dict) -> str:
    """Format a human-readable description of a migration candidate."""
    parts = [candidate["provider"].get("label", "?")]
    if candidate.get("source"):
        parts.append(f"at {candidate['source']}")
    return " ".join(parts)


def _log_migration_hint(runtime: Any, candidate: dict) -> None:
    """Log a hint about available migration (non-interactive fallback)."""
    description = _describe_candidate(candidate)
    provider_id = candidate["provider"].get("id", "?")
    logger.info(f"Detected {description}. Preview migration with: hermes migrate {provider_id} --dry-run")


async def _run_migration(
    provider: dict,
    source: Optional[str],
    config: dict,
    runtime: Any,
) -> dict:
    """Run a migration using the provider."""
    # This would call the provider's prepareApply and migrate command
    logger.info(f"Running migration for {provider.get('label', '?')}")
    return {"items": []}


def _apply_config_patches(config: dict, result: dict) -> dict:
    """Apply config patches from a migration result."""
    import copy
    items = result.get("items", [])
    patches = [
        item for item in items
        if isinstance(item, dict)
        and item.get("kind") == "config"
        and item.get("action") == "merge"
        and item.get("status") == "migrated"
    ]

    if not patches:
        return config

    next_config = copy.deepcopy(config)
    for patch in patches:
        path = patch.get("path", "")
        value = patch.get("value")
        if path and value is not None:
            _set_nested(next_config, path.split("."), value)

    return next_config


def _set_nested(d: dict, keys: list[str], value: Any) -> None:
    """Set a nested value in a dict by key path."""
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
