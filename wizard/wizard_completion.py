"""
wizard_completion.py — Shell completion installation during setup.

Adapted from OpenClaw src/wizard/setup.completion.ts.

Offers to install shell completion for the CLI during the setup wizard.
Hermes has hermes_cli/completion.py (generates scripts) but lacks the
setup flow integration (detect shell, generate cache, install profile).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ShellCompletionStatus:
    """Detected shell completion state."""
    def __init__(self, shell: str, profile_installed: bool, uses_slow_pattern: bool, cache_exists: bool):
        self.shell = shell
        self.profile_installed = profile_installed
        self.uses_slow_pattern = uses_slow_pattern
        self.cache_exists = cache_exists


class CompletionInstaller:
    """Installs shell completion for the CLI into the user's profile."""

    SHELL_PROFILES = {
        "bash": ["~/.bashrc", "~/.bash_profile"],
        "zsh": ["~/.zshrc"],
        "fish": ["~/.config/fish/config.fish"],
    }

    def __init__(self, cli_name: str = "hermes"):
        self.cli_name = cli_name

    def check_status(self) -> ShellCompletionStatus:
        """Detect current shell completion status."""
        shell = self._detect_shell()
        if shell == "unknown":
            return ShellCompletionStatus(shell="unknown", profile_installed=False, uses_slow_pattern=False, cache_exists=False)

        profile_installed = self._check_profile_installed(shell)
        uses_slow_pattern = self._check_slow_pattern(shell) if profile_installed else False
        cache_exists = self._check_cache_exists(shell)

        return ShellCompletionStatus(
            shell=shell,
            profile_installed=profile_installed,
            uses_slow_pattern=uses_slow_pattern,
            cache_exists=cache_exists,
        )

    def _detect_shell(self) -> str:
        """Detect the user's current shell from environment."""
        shell_path = os.environ.get("SHELL", "")
        if "zsh" in shell_path:
            return "zsh"
        if "bash" in shell_path:
            return "bash"
        if "fish" in shell_path:
            return "fish"
        if sys.platform == "win32":
            return "powershell"
        return "unknown"

    def _check_profile_installed(self, shell: str) -> bool:
        """Check if completion is already installed in the shell profile."""
        profiles = self.SHELL_PROFILES.get(shell, [])
        for profile_path in profiles:
            expanded = Path(profile_path).expanduser()
            if expanded.exists():
                content = expanded.read_text()
                if f"{self.cli_name} completion" in content or f"_{self.cli_name}_completion" in content:
                    return True
        return False

    def _check_slow_pattern(self, shell: str) -> bool:
        """Check if profile uses slow dynamic completion pattern."""
        profiles = self.SHELL_PROFILES.get(shell, [])
        for profile_path in profiles:
            expanded = Path(profile_path).expanduser()
            if expanded.exists():
                content = expanded.read_text()
                # Slow pattern: calls binary on every shell startup
                if f"eval \"$({self.cli_name} completion" in content and "--cache" not in content:
                    return True
        return False

    def _check_cache_exists(self, shell: str) -> bool:
        """Check if completion cache file exists."""
        cache_dir = Path.home() / ".hermes" / "completion_cache"
        cache_file = cache_dir / f"{shell}.cache"
        return cache_file.exists()

    def ensure_cache(self) -> bool:
        """Generate completion cache file. Returns True on success."""
        try:
            cache_dir = Path.home() / ".hermes" / "completion_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            shell = self._detect_shell()
            cache_file = cache_dir / f"{shell}.cache"

            # Generate completion text by running the CLI
            import subprocess
            result = subprocess.run(
                [self.cli_name, "completion", shell],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                cache_file.write_text(result.stdout)
                logger.info(f"Completion cache generated: {cache_file}")
                return True
            else:
                logger.warning(f"Failed to generate completion cache: {result.stderr}")
                return False
        except Exception as e:
            logger.warning(f"Cache generation error: {e}")
            return False

    def install_to_profile(self, shell: str) -> bool:
        """Install completion into the user's shell profile."""
        profiles = self.SHELL_PROFILES.get(shell, [])
        if not profiles:
            logger.warning(f"No known profiles for shell: {shell}")
            return False

        # Find first existing profile to install into
        target: Optional[Path] = None
        for profile_path in profiles:
            expanded = Path(profile_path).expanduser()
            if expanded.exists():
                target = expanded
                break

        # If none exist, use the first one
        if target is None:
            target = Path(profiles[0]).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)

        # Generate cache first (required for fast shell startup)
        if not self.ensure_cache():
            return False

        try:
            cache_dir = Path.home() / ".hermes" / "completion_cache"
            cache_file = cache_dir / f"{shell}.cache"
            completion_line = f'\n# Hermes shell completion (cached)\nsource "{cache_file}" 2>/dev/null\n'

            content = target.read_text() if target.exists() else ""
            if completion_line.strip() in content:
                logger.info("Completion already in profile")
                return True

            with open(target, "a") as f:
                f.write(completion_line)
            logger.info(f"Completion installed to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to install completion: {e}")
            return False


def setup_wizard_completion(
    cli_name: str = "hermes",
    auto_install: bool = False,
    prompter=None,
) -> bool:
    """
    Run the setup wizard's shell completion step.

    - Detects shell and current completion state
    - If slow pattern: silently upgrade to cached version
    - If profile installed but no cache: auto-fix silently
    - If no completion: offer to install (or auto-install in quickstart)
    """
    installer = CompletionInstaller(cli_name)
    status = installer.check_status()

    if status.shell == "unknown":
        return False

    # Case 1: Slow dynamic pattern — silently upgrade
    if status.uses_slow_pattern:
        if installer.ensure_cache():
            installer.install_to_profile(status.shell)
        return True

    # Case 2: Profile has completion but no cache — auto-fix
    if status.profile_installed and not status.cache_exists:
        installer.ensure_cache()
        return True

    # Case 3: No completion at all — offer to install
    if not status.profile_installed:
        should_install = auto_install
        if not auto_install and prompter:
            from .wizard_i18n import t
            should_install = prompter.confirm(
                message=t("wizard.completion.enable", {"shell": status.shell, "cli": cli_name}),
                default=True,
            )
        elif not auto_install:
            # Non-interactive: skip
            return False

        if should_install:
            return installer.install_to_profile(status.shell)

    return True
