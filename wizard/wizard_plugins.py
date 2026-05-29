"""
wizard_plugins.py — Plugin installation during onboarding.

Adapted from OpenClaw src/wizard/setup.official-plugins.ts.

Lists official external plugin catalog entries and offers installation
during the setup wizard. Hermes has plugins_cmd.py for managing plugins
but lacks the official catalog with curated plugin selection during setup.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PluginInstall:
    """Represents a plugin installation source."""
    def __init__(self, clawhub_spec: Optional[str] = None, npm_spec: Optional[str] = None,
                 local_path: Optional[str] = None, default_choice: str = "npm"):
        self.clawhub_spec = clawhub_spec
        self.npm_spec = npm_spec
        self.local_path = local_path
        self.default_choice = default_choice


class OfficialPluginEntry:
    """An official plugin available for onboarding installation."""
    def __init__(self, plugin_id: str, label: str, description: Optional[str] = None,
                 install: Optional[PluginInstall] = None):
        self.plugin_id = plugin_id
        self.label = label
        self.description = description
        self.install = install or PluginInstall()
        self.trusted_source_linked_official_install = True


# Official external plugin catalog
# In OpenClaw this is loaded from a registry; here we define a static catalog
# that can be extended by reading from a catalog file or registry API.
_OFFICIAL_CATALOG: list[dict[str, Any]] = [
    # Example entries — in production these come from ClawHub or OpenClaw registry
    # {
    #     "source": "official",
    #     "kind": "plugin",
    #     "plugin": {"id": "hermes-memory-enhanced", "name": "Enhanced Memory"},
    #     "description": "Advanced memory with vector search and embeddings",
    #     "install": {"npm": "@openclaw/plugin-memory-enhanced", "clawhub": "openclaw/memory-enhanced"},
    # },
]


def load_catalog_from_file(path: str = "~/.hermes/plugin-catalog.json") -> list[dict]:
    """Load official plugin catalog from a local file."""
    catalog_path = Path(path).expanduser()
    if catalog_path.exists():
        return json.loads(catalog_path.read_text())
    return _OFFICIAL_CATALOG


def list_official_plugins(
    config: dict,
    catalog_path: Optional[str] = None,
) -> list[OfficialPluginEntry]:
    """
    List official plugins that are not yet installed or configured.

    Filters out plugins already present in config.plugins.entries or
    config.plugins.installs.
    """
    installed_ids = set()
    plugins_config = config.get("plugins", {})
    if isinstance(plugins_config, dict):
        entries = plugins_config.get("entries", {})
        installs = plugins_config.get("installs", {})
        if isinstance(entries, dict):
            installed_ids.update(entries.keys())
        if isinstance(installs, dict):
            installed_ids.update(installs.keys())

    catalog = load_catalog_from_file(catalog_path) if catalog_path else _OFFICIAL_CATALOG
    entries = []

    for item in catalog:
        if item.get("source") != "official" or item.get("kind") != "plugin":
            continue
        plugin_info = item.get("plugin", {})
        if not plugin_info.get("id"):
            continue
        # Skip if it has channel or provider fields (those are channel plugins, not generic)
        if item.get("channel"):
            continue
        if item.get("providers"):
            continue
        if item.get("webSearchProviders"):
            continue

        plugin_id = plugin_info["id"]
        if plugin_id in installed_ids:
            continue

        install_info = item.get("install", {})
        install = PluginInstall(
            clawhub_spec=install_info.get("clawhub"),
            npm_spec=install_info.get("npm"),
            local_path=install_info.get("local"),
            default_choice=install_info.get("default", "npm"),
        )

        entries.append(OfficialPluginEntry(
            plugin_id=plugin_id,
            label=plugin_info.get("name", plugin_id),
            description=item.get("description"),
            install=install,
        ))

    entries.sort(key=lambda e: e.label)
    return entries


def format_install_hint(install: PluginInstall) -> str:
    """Format a human-readable hint about install sources."""
    if install.clawhub_spec and install.npm_spec:
        return f"{'ClawHub' if install.default_choice == 'clawhub' else 'npm'}, with fallback"
    if install.clawhub_spec:
        return "ClawHub"
    if install.npm_spec:
        return "npm"
    if install.local_path:
        return "local path"
    return "install source"


async def install_official_plugins(
    config: dict,
    selected_ids: list[str],
    prompter=None,
    workspace_dir: Optional[str] = None,
) -> dict:
    """
    Install selected official plugins and return updated config.

    Each plugin is installed via npm or ClawHub, then enabled in config.
    """
    import copy
    entries = list_official_plugins(config)
    next_config = copy.deepcopy(config)

    for plugin_id in selected_ids:
        if plugin_id == "__skip__":
            continue

        entry = next((e for e in entries if e.plugin_id == plugin_id), None)
        if not entry:
            logger.warning(f"Unknown plugin: {plugin_id}")
            continue

        logger.info(f"Installing {entry.label}...")

        try:
            success = await _install_plugin(entry)
            if success:
                # Enable in config
                if "plugins" not in next_config:
                    next_config["plugins"] = {}
                if "entries" not in next_config["plugins"]:
                    next_config["plugins"]["entries"] = {}
                next_config["plugins"]["entries"][plugin_id] = {"enabled": True}
                logger.info(f"Installed {entry.label}")
                if prompter:
                    prompter.note(f"Installed {entry.label} plugin")
            else:
                logger.warning(f"Failed to install {entry.label}")
        except Exception as e:
            logger.error(f"Error installing {entry.label}: {e}")

    return next_config


async def _install_plugin(entry: OfficialPluginEntry) -> bool:
    """Install a single plugin via its preferred install method."""
    install = entry.install

    # Try primary method
    if install.default_choice == "clawhub" and install.clawhub_spec:
        return await _install_via_clawhub(install.clawhub_spec)
    elif install.npm_spec:
        return await _install_via_npm(install.npm_spec)
    elif install.clawhub_spec:
        return await _install_via_clawhub(install.clawhub_spec)
    elif install.local_path:
        return await _install_via_local(install.local_path)

    return False


async def _install_via_npm(spec: str) -> bool:
    """Install a plugin via npm."""
    try:
        proc = subprocess.run(
            ["npm", "install", "-g", spec],
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"npm install failed: {e}")
        return False


async def _install_via_clawhub(spec: str) -> bool:
    """Install a plugin via ClawHub."""
    try:
        proc = subprocess.run(
            ["openclaw", "plugins", "install", spec],
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"ClawHub install failed: {e}")
        return False


async def _install_via_local(path: str) -> bool:
    """Install a plugin from a local path."""
    expanded = Path(path).expanduser()
    if not expanded.exists():
        logger.error(f"Local plugin path does not exist: {expanded}")
        return False
    try:
        # Copy to plugins directory
        plugins_dir = Path("~/.hermes/plugins").expanduser()
        plugins_dir.mkdir(parents=True, exist_ok=True)
        target = plugins_dir / expanded.name
        if expanded.is_dir():
            import shutil
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(expanded, target)
        else:
            import shutil
            shutil.copy2(expanded, target)
        return True
    except Exception as e:
        logger.error(f"Local install failed: {e}")
        return False
