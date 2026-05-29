"""
Pluggable implementation registry for Hermes.

Allows swapping implementations via config string instead of code changes.

Usage:
    # In config.yaml
    agent.skill_runner = "hermes.custom.MyCustomRunner"

    # In code
    from agent.pluggable import get_impl
    runner = get_impl(BaseRunner, config["agent"]["skill_runner"])

Based on OpenHands app_server/utils/import_utils.py pattern.
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


class ImplementationRegistry:
    """Global registry for pluggable implementations.

    Register implementations by string key, retrieve by base class + key.
    Falls back to ``module.ClassName`` dynamic import if not pre-registered.
    """

    _registry: Dict[str, Any] = {}

    @classmethod
    def register(cls, key: str, impl: Any) -> None:
        """Register an implementation under a string key."""
        cls._registry[key] = impl
        logger.debug("pluggable: registered '%s' -> %s", key, type(impl).__name__)

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Look up a pre-registered implementation by key."""
        return cls._registry.get(key)

    @classmethod
    def list_registered(cls) -> Dict[str, str]:
        """Return {key: class_name} for all registered implementations."""
        return {k: type(v).__name__ for k, v in cls._registry.items()}


def get_impl(base_class: Type, class_spec: str) -> Any:
    """Return an implementation instance.

    Resolution order:
    1. Check pre-registered implementations (by exact key match)
    2. Dynamic import from ``module.ClassName`` string

    Args:
        base_class: ABC that the implementation must subclass.
        class_spec: Either a registry key or ``"module.ClassName"``.

    Returns:
        An instance of the implementation class.

    Raises:
        ValueError: If the class can't be found or doesn't subclass base_class.
    """
    # 1. Registry lookup
    registered = ImplementationRegistry.get(class_spec)
    if registered is not None:
        if isinstance(registered, type):
            return registered()
        return registered  # already an instance

    # 2. Dynamic import: "module.ClassName"
    if "." not in class_spec:
        raise ValueError(
            f"Cannot resolve '{class_spec}': not a registry key and "
            f"not a dotted module.ClassName path."
        )

    module_path, class_name = class_spec.rsplit(".", 1)
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ValueError(
            f"Cannot import module '{module_path}' for '{class_spec}': {exc}"
        ) from exc

    try:
        impl_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise ValueError(
            f"Module '{module_path}' has no class '{class_name}'"
        ) from exc

    if isinstance(impl_cls, type) and not issubclass(impl_cls, base_class):
        raise ValueError(
            f"{class_spec} ({type(impl_cls).__name__}) is not a subclass of "
            f"{base_class.__name__}"
        )

    if isinstance(impl_cls, type):
        return impl_cls()
    return impl_cls  # already an instance
