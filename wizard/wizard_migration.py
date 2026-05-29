"""
wizard_migration.py — Migration import during setup/onboarding.

Adapted from OpenClaw src/wizard/setup.migration-import.ts.

Allows importing config, credentials, sessions, and workspace from
other agent systems during onboarding. Hermes has no equivalent —
this is a new feature worth porting.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


class MigrationProvider(Protocol):
    """Protocol for migration providers (plugins that can detect and import from other systems)."""
    id: str
    label: str
    description: Optional[str]

    async def detect(self, config: dict, state_dir: str, logger: Any) -> "MigrationDetection": ...
    async def plan(self, ctx: "MigrationContext") -> "MigrationPlan": ...
    async def apply(self, ctx: "MigrationContext", plan: "MigrationPlan") -> "MigrationResult": ...


class MigrationDetection:
    def __init__(self, found: bool, label: Optional[str] = None, source: Optional[str] = None,
                 message: Optional[str] = None, confidence: str = "high"):
        self.found = found
        self.label = label
        self.source = source
        self.message = message
        self.confidence = confidence  # "high" or "low"


class MigrationContext:
    def __init__(self, config: dict, state_dir: str, source: str,
                 include_secrets: bool = False, overwrite: bool = False,
                 logger: Any = None, backup_path: Optional[str] = None,
                 report_dir: Optional[str] = None):
        self.config = config
        self.state_dir = state_dir
        self.source = source
        self.include_secrets = include_secrets
        self.overwrite = overwrite
        self.logger = logger
        self.backup_path = backup_path
        self.report_dir = report_dir


class MigrationPlanItem:
    def __init__(self, kind: str, action: str, path: str, status: str = "pending", details: Any = None):
        self.kind = kind  # "config", "credential", "session", "workspace"
        self.action = action  # "merge", "overwrite", "skip"
        self.path = path
        self.status = status
        self.details = details


class MigrationPlan:
    def __init__(self, items: list[MigrationPlanItem], conflicts: list[str] | None = None):
        self.items = items
        self.conflicts = conflicts or []


class MigrationResult:
    def __init__(self, success: bool, items: list[MigrationPlanItem],
                 backup_path: Optional[str] = None, report_dir: Optional[str] = None):
        self.success = success
        self.items = items
        self.backup_path = backup_path
        self.report_dir = report_dir


class SetupMigration:
    """Handles migration import during the setup wizard onboarding flow."""

    def __init__(self, config: dict, state_dir: str,
                 workspace_dir: str = "~/.hermes/workspace"):
        self.config = config
        self.state_dir = state_dir
        self.workspace_dir = str(Path(workspace_dir).expanduser())

    async def detect_sources(self, providers: list[MigrationProvider]) -> list[MigrationDetection]:
        """Detect available migration sources from registered providers."""
        detections = []
        for provider in providers:
            if not hasattr(provider, "detect"):
                continue
            try:
                detection = await provider.detect(
                    config=self.config,
                    state_dir=self.state_dir,
                    logger=logger,
                )
                if detection.found:
                    detections.append(detection)
            except Exception as e:
                logger.debug(f"Migration provider {provider.id} detection failed: {e}")
        return detections

    async def check_freshness(self) -> tuple[bool, list[str]]:
        """
        Check if this is a fresh setup suitable for migration import.
        Returns (fresh, reasons) where reasons is a list of existing items.
        """
        reasons = []

        # Check for meaningful config values
        ignored_keys = {"$schema", "meta"}
        if any(k for k in self.config if k not in ignored_keys):
            reasons.append("existing config values are loaded")

        # Check workspace entries
        workspace_entries = ["AGENTS.md", "SOUL.md", "USER.md", "IDENTITY.md", "MEMORY.md", "skills"]
        ws = Path(self.workspace_dir)
        for entry in workspace_entries:
            if (ws / entry).exists():
                reasons.append(f"workspace {entry} exists")

        # Check state directories
        state_entries = ["credentials", "sessions", "agents"]
        for entry in state_entries:
            entry_path = Path(self.state_dir) / entry
            if entry_path.exists() and any(entry_path.iterdir()):
                reasons.append(f"state {entry}/ exists")

        fresh = len(reasons) == 0
        return fresh, reasons

    async def run_import(
        self,
        provider: MigrationProvider,
        source: str,
        workspace_dir: str,
        include_secrets: bool = False,
        prompter=None,
        non_interactive: bool = False,
    ) -> dict:
        """
        Run the full migration import flow:
        1. Freshness check
        2. Plan migration
        3. Show preview
        4. Confirm
        5. Create backup
        6. Apply
        7. Show result

        Returns the updated config dict.
        """
        import copy
        config = copy.deepcopy(self.config)

        # Step 1: Freshness check
        fresh, reasons = await self.check_freshness()
        if fresh or os.environ.get("OPENCLAW_MIGRATION_EXISTING_IMPORT") == "1":
            pass
        else:
            raise ValueError(
                "Migration import during onboarding requires a fresh setup.\n"
                "Create a fresh setup or reset config, credentials, sessions, and workspace.\n"
                f"Existing setup:\n" + "\n".join(f"- {r}" for r in reasons)
            )

        # Step 2: Build context and plan
        ctx = MigrationContext(
            config=config,
            state_dir=self.state_dir,
            source=source,
            include_secrets=include_secrets,
            overwrite=False,
            logger=logger,
        )
        plan = await provider.plan(ctx)

        # Step 3: Show preview
        preview_lines = [f"[{item.kind}] {item.path}: {item.action}" for item in plan.items]
        logger.info("Migration preview:")
        for line in preview_lines:
            logger.info(f"  {line}")

        if prompter:
            from .wizard_i18n import t
            await prompter.note("\n".join(preview_lines), t("wizard.migration.previewTitle"))

        # Check for conflicts
        if plan.conflicts:
            raise ValueError(
                f"Cannot migrate: unresolved conflicts:\n" +
                "\n".join(f"- {c}" for c in plan.conflicts)
            )

        # Step 4: Confirm
        confirmed = True
        if not non_interactive and prompter:
            from .wizard_i18n import t
            confirmed = prompter.confirm(
                message=t("wizard.migration.apply"),
                default=False,
            )

        if not confirmed:
            from .wizard_prompts import WizardCancelledError
            raise WizardCancelledError("Migration cancelled")

        # Step 5: Create backup
        backup_path = self._create_backup()

        # Step 6: Apply
        result = await provider.apply(
            MigrationContext(
                config=ctx.config,
                state_dir=ctx.state_dir,
                source=ctx.source,
                include_secrets=ctx.include_secrets,
                overwrite=ctx.overwrite,
                logger=ctx.logger,
                backup_path=backup_path,
            ),
            plan,
        )

        # Step 7: Show result
        result_lines = [
            f"Migration {'succeeded' if result.success else 'failed'}",
            f"  Items processed: {len(result.items)}",
        ]
        if result.backup_path:
            result_lines.append(f"  Backup: {result.backup_path}")
        if result.report_dir:
            result_lines.append(f"  Report: {result.report_dir}")

        for line in result_lines:
            logger.info(line)

        if prompter:
            from .wizard_i18n import t
            await prompter.note("\n".join(result_lines), t("wizard.migration.appliedTitle"))
            await prompter.outro(t("wizard.migration.complete"))

        return ctx.config

    def _create_backup(self) -> str:
        """Create a pre-migration backup of config and state."""
        from datetime import datetime
        backup_dir = Path(self.state_dir) / "backups" / f"pre-migration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup config
        config_path = Path(self.config.get("_config_path", "~/.hermes/config.yaml")).expanduser()
        if config_path.exists():
            shutil.copy2(config_path, backup_dir / "config.yaml")

        # Backup credentials
        creds_dir = Path(self.state_dir) / "credentials"
        if creds_dir.exists():
            shutil.copytree(creds_dir, backup_dir / "credentials")

        logger.info(f"Backup created at {backup_dir}")
        return str(backup_dir)
