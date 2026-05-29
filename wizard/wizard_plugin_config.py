"""
wizard_plugin_config.py — Plugin configuration via uiHints during setup.

Adapted from OpenClaw src/wizard/setup.plugin-config.ts.

Discovers configurable plugins (with non-advanced uiHints) and prompts
the user to configure their fields during onboarding. Hermes has no
equivalent — plugins are configured manually via config files.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


class PluginConfigUiHint:
    """uiHint from a plugin manifest for a config field."""
    def __init__(self, label: Optional[str] = None, help: Optional[str] = None,
                 advanced: bool = False, sensitive: bool = False,
                 placeholder: Optional[str] = None):
        self.label = label
        self.help = help
        self.advanced = advanced
        self.sensitive = sensitive
        self.placeholder = placeholder


class ConfigurablePlugin:
    """A discovered plugin with configurable fields via uiHints."""
    def __init__(self, plugin_id: str, name: str,
                 ui_hints: dict[str, PluginConfigUiHint],
                 json_schema: Optional[dict] = None):
        self.id = plugin_id
        self.name = name
        self.ui_hints = ui_hints
        self.json_schema = json_schema


def discover_configurable_plugins(
    manifest_plugins: list[dict[str, Any]],
) -> list[ConfigurablePlugin]:
    """
    Discover plugins that have non-advanced uiHints fields.
    Returns only plugins with at least one promptable field.
    """
    result = []
    for plugin in manifest_plugins:
        ui_hints_raw = plugin.get("configUiHints")
        if not ui_hints_raw:
            continue

        # Filter to non-advanced fields only
        promptable: dict[str, PluginConfigUiHint] = {}
        for key, hint_raw in ui_hints_raw.items():
            hint = PluginConfigUiHint(
                label=hint_raw.get("label"),
                help=hint_raw.get("help"),
                advanced=hint_raw.get("advanced", False),
                sensitive=hint_raw.get("sensitive", False),
                placeholder=hint_raw.get("placeholder"),
            )
            if not hint.advanced:
                promptable[key] = hint

        if not promptable:
            continue

        result.append(ConfigurablePlugin(
            plugin_id=plugin["id"],
            name=plugin.get("name", plugin["id"]),
            ui_hints=promptable,
            json_schema=plugin.get("configSchema"),
        ))

    result.sort(key=lambda p: p.name)
    return result


def discover_unconfigured_plugins(
    manifest_plugins: list[dict[str, Any]],
    config: dict,
) -> list[ConfigurablePlugin]:
    """
    Discover plugins with unconfigured non-advanced fields.
    Returns only plugins where at least one promptable field has no value.
    """
    all_plugins = discover_configurable_plugins(manifest_plugins)
    result = []

    for plugin in all_plugins:
        existing = get_plugin_config(config, plugin.id)
        has_unconfigured = False
        for key in plugin.ui_hints:
            val = _get_nested(existing, key.split("."))
            if val is None or val == "":
                has_unconfigured = True
                break
        if has_unconfigured:
            result.append(plugin)

    return result


def get_plugin_config(config: dict, plugin_id: str) -> dict:
    """Get the config dict for a specific plugin from the full config."""
    plugins = config.get("plugins", {})
    if isinstance(plugins, dict):
        entries = plugins.get("entries", {})
        if isinstance(entries, dict):
            entry = entries.get(plugin_id, {})
            if isinstance(entry, dict):
                return entry.get("config", {})
    return {}


def _get_nested(d: dict, keys: list[str]) -> Any:
    """Get a nested value from a dict by key path."""
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _set_nested(d: dict, keys: list[str], value: Any) -> None:
    """Set a nested value in a dict by key path, creating intermediate dicts."""
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _format_current_value(value: Any) -> str:
    """Format a config value for display."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


async def prompt_plugin_fields(
    plugin: ConfigurablePlugin,
    config: dict,
    prompter,
    show_configured: bool = False,
) -> dict:
    """
    Prompt the user to configure a single plugin's fields via uiHints.
    Returns the updated config with plugin values applied.
    """
    existing = get_plugin_config(config, plugin.id)
    updated = copy.deepcopy(existing)
    changed = False

    for key, hint in plugin.ui_hints.items():
        path_segments = key.split(".")
        current_value = _get_nested(existing, path_segments)
        has_value = current_value is not None and current_value != ""

        # In onboard mode, skip already-configured fields
        if has_value and not show_configured:
            continue

        label = hint.label or key
        help_suffix = f" — {hint.help}" if hint.help else ""

        # Skip sensitive fields — direct users to config set or Web UI
        if hint.sensitive:
            logger.info(f"Skipping sensitive field {plugin.id}.{key}")
            continue

        # Resolve schema for type info
        schema_prop = _resolve_schema_prop(plugin.json_schema, key)

        # Handle enum fields with select
        if schema_prop and "enum" in schema_prop and isinstance(schema_prop["enum"], list):
            options = [{"value": str(v), "label": str(v)} for v in schema_prop["enum"]]
            if has_value:
                options.insert(0, {"value": "__keep__", "label": f"Keep current ({_format_current_value(current_value)})"})

            selected = prompter.select(
                message=f"{label}{help_suffix}",
                options=options,
                initial="__keep__" if has_value else None,
            )
            if selected != "__keep__":
                _set_nested(updated, path_segments, selected)
                changed = True
            continue

        # Handle boolean fields with confirm
        if schema_prop and schema_prop.get("type") == "boolean":
            confirmed = prompter.confirm(
                message=f"{label}{help_suffix}",
                default=bool(current_value) if isinstance(current_value, bool) else False,
            )
            if confirmed != current_value:
                _set_nested(updated, path_segments, confirmed)
                changed = True
            continue

        # Handle array fields — prompt as comma-separated string
        if schema_prop and schema_prop.get("type") == "array":
            current_str = ", ".join(str(v) for v in current_value) if isinstance(current_value, list) else ""
            input_val = prompter.text(
                message=f"{label} (comma-separated, empty to clear){help_suffix}",
                initial=current_str,
                placeholder=hint.placeholder or "value1, value2",
            )
            trimmed = input_val.strip()
            if trimmed != current_str:
                if trimmed:
                    values = [v.strip() for v in trimmed.split(",") if v.strip()]
                    _set_nested(updated, path_segments, values)
                else:
                    _set_nested(updated, path_segments, None)
                changed = True
            continue

        # Default: text input (string, number, etc.)
        current_str = _format_current_value(current_value)
        input_val = prompter.text(
            message=f"{label}{help_suffix}",
            initial=current_str,
            placeholder=hint.placeholder,
        )
        trimmed = input_val.strip()
        if trimmed != current_str:
            # Coerce numeric input
            if schema_prop and schema_prop.get("type") in ("number", "integer"):
                if trimmed == "":
                    _set_nested(updated, path_segments, None)
                    changed = True
                else:
                    try:
                        num = float(trimmed)
                        if schema_prop.get("type") == "integer":
                            num = int(num)
                        _set_nested(updated, path_segments, num)
                        changed = True
                    except ValueError:
                        pass
            else:
                _set_nested(updated, path_segments, trimmed or None)
                changed = True

    if not changed:
        return config

    # Merge updated plugin config back into the full config
    result = copy.deepcopy(config)
    if "plugins" not in result:
        result["plugins"] = {}
    if "entries" not in result["plugins"]:
        result["plugins"]["entries"] = {}
    if plugin.id not in result["plugins"]["entries"]:
        result["plugins"]["entries"][plugin.id] = {}
    result["plugins"]["entries"][plugin.id]["config"] = updated
    return result


def _resolve_schema_prop(json_schema: Optional[dict], field_key: str) -> Optional[dict]:
    """Resolve a JSON schema property by dot-separated field key."""
    if not json_schema:
        return None
    current: Any = json_schema
    for segment in field_key.split("."):
        if not isinstance(current, dict):
            return None
        props = current.get("properties")
        if not isinstance(props, dict):
            return None
        current = props.get(segment)
    return current if isinstance(current, dict) else None


async def setup_plugin_config(
    config: dict,
    manifest_plugins: list[dict[str, Any]],
    prompter,
) -> dict:
    """
    Run the plugin configuration step for the onboard wizard.
    Shows unconfigured plugin fields and prompts the user.
    """
    unconfigured = discover_unconfigured_plugins(manifest_plugins, config)

    if not unconfigured:
        return config

    # Let user select which plugins to configure
    options = [
        {"value": "__skip__", "label": "Skip for now", "hint": "Continue without configuring plugins"},
    ]
    for p in unconfigured:
        field_count = len(p.ui_hints)
        options.append({
            "value": p.id,
            "label": p.name,
            "hint": f"{field_count} field{'s' if field_count != 1 else ''}",
        })

    selected = prompter.multiselect(
        message="Configure plugins (select to set up now, or skip)",
        options=options,
    )

    result_config = config
    for plugin_id in selected:
        if plugin_id == "__skip__":
            continue
        plugin = next((p for p in unconfigured if p.id == plugin_id), None)
        if not plugin:
            continue

        prompter.note(f"Configure {plugin.name}", "Plugin setup")
        result_config = await prompt_plugin_fields(plugin, result_config, prompter)

    return result_config
