"""Tool availability evaluation.

Ported from OpenClaw src/tools/availability.ts

Evaluates whether a tool should be available based on a declarative
availability expression and a runtime context (auth, config, env, plugins).
"""

from __future__ import annotations

from .types import (
    JsonValue,
    ToolAvailabilityContext,
    ToolAvailabilityDiagnostic,
    ToolAvailabilityExpression,
    ToolAvailabilitySignal,
    ToolAvailabilitySignalKind,
    ToolDescriptor,
    ToolUnavailableReason,
)


def _is_record(value: JsonValue | None) -> bool:
    return isinstance(value, dict) and not isinstance(value, list)


def _resolve_config_path(
    config: JsonValue | None,
    path: list[str],
) -> JsonValue | None:
    """Walk a dotted path into a config dict to resolve a value."""
    current: JsonValue | None = config
    for segment in path:
        if not _is_record(current):
            return None
        current = current.get(segment)
    return current


def _has_configured_value(
    value: JsonValue | None,
    signal: ToolAvailabilitySignal,
    context: ToolAvailabilityContext,
) -> bool:
    """Check if a config value meets the availability check."""
    if value is None:
        return False
    check = signal.check or "exists"
    if check == "available":
        fn = context.is_config_value_available
        if fn is not None:
            return fn(value=value, path=signal.path, signal=signal)
        return False
    if check == "exists":
        return True
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _make_diagnostic(
    reason: ToolUnavailableReason,
    signal: ToolAvailabilitySignal | None,
    message: str,
) -> ToolAvailabilityDiagnostic:
    return ToolAvailabilityDiagnostic(
        reason=reason,
        signal=signal,
        message=message,
    )


def _evaluate_signal(
    signal: ToolAvailabilitySignal,
    context: ToolAvailabilityContext,
) -> ToolAvailabilityDiagnostic | None:
    """Evaluate a single availability signal. Returns None if available."""
    match signal.kind:
        case ToolAvailabilitySignalKind.ALWAYS:
            return None

        case ToolAvailabilitySignalKind.AUTH:
            if context.auth_provider_ids and signal.provider_id in context.auth_provider_ids:
                return None
            return _make_diagnostic(
                ToolUnavailableReason.AUTH_MISSING,
                signal,
                f"Missing auth provider: {signal.provider_id}",
            )

        case ToolAvailabilitySignalKind.CONFIG:
            value = _resolve_config_path(context.config, signal.path)
            if _has_configured_value(value, signal, context):
                return None
            return _make_diagnostic(
                ToolUnavailableReason.CONFIG_MISSING,
                signal,
                f"Missing config path: {".".join(signal.path)}",
            )

        case ToolAvailabilitySignalKind.ENV:
            env_val = (context.env or {}).get(signal.name or "")
            if env_val and env_val.strip():
                return None
            return _make_diagnostic(
                ToolUnavailableReason.ENV_MISSING,
                signal,
                f"Missing environment value: {signal.name}",
            )

        case ToolAvailabilitySignalKind.PLUGIN_ENABLED:
            if (
                context.enabled_plugin_ids
                and signal.plugin_id in context.enabled_plugin_ids
            ):
                return None
            return _make_diagnostic(
                ToolUnavailableReason.PLUGIN_DISABLED,
                signal,
                f"Plugin is not enabled: {signal.plugin_id}",
            )

        case ToolAvailabilitySignalKind.CONTEXT:
            ctx_values = context.values or {}
            value = ctx_values.get(signal.key)
            if signal.equals is None:
                if value is not None:
                    return None
                return _make_diagnostic(
                    ToolUnavailableReason.CONTEXT_MISMATCH,
                    signal,
                    f"Missing context value: {signal.key}",
                )
            if value == signal.equals:
                return None
            return _make_diagnostic(
                ToolUnavailableReason.CONTEXT_MISMATCH,
                signal,
                f"Context value did not match: {signal.key}",
            )

        case _:
            return _make_diagnostic(
                ToolUnavailableReason.UNSUPPORTED_SIGNAL,
                signal,
                "Unsupported availability signal",
            )


def _evaluate_expression(
    expression: ToolAvailabilityExpression,
    context: ToolAvailabilityContext,
) -> list[ToolAvailabilityDiagnostic]:
    """Recursively evaluate an availability expression."""
    if expression.signal is not None:
        result = _evaluate_signal(expression.signal, context)
        return [result] if result is not None else []

    if expression.all_of is not None:
        if len(expression.all_of) == 0:
            return [
                ToolAvailabilityDiagnostic(
                    reason=ToolUnavailableReason.UNSUPPORTED_SIGNAL,
                    message="Empty availability allOf group",
                )
            ]
        results: list[ToolAvailabilityDiagnostic] = []
        for entry in expression.all_of:
            results.extend(_evaluate_expression(entry, context))
        return results

    if expression.any_of is not None:
        if len(expression.any_of) == 0:
            return [
                ToolAvailabilityDiagnostic(
                    reason=ToolUnavailableReason.UNSUPPORTED_SIGNAL,
                    message="Empty availability anyOf group",
                )
            ]
        all_diagnostics = [
            _evaluate_expression(entry, context) for entry in expression.any_of
        ]
        if any(len(d) == 0 for d in all_diagnostics):
            return []  # At least one branch passed
        results: list[ToolAvailabilityDiagnostic] = []
        for d in all_diagnostics:
            results.extend(d)
        return results

    return [
        ToolAvailabilityDiagnostic(
            reason=ToolUnavailableReason.UNSUPPORTED_SIGNAL,
            message="Unsupported availability expression",
        )
    ]


def evaluate_tool_availability(
    descriptor: ToolDescriptor,
    context: ToolAvailabilityContext | None = None,
) -> list[ToolAvailabilityDiagnostic]:
    """Evaluate whether a tool is available given a context.

    Returns an empty list if the tool is available, or a list of diagnostics
    explaining why it is not.
    """
    ctx = context or ToolAvailabilityContext()
    availability = descriptor.availability
    if availability is None:
        return []

    expression = _sanitize_availability_expression(availability)
    if expression is None:
        return [
            ToolAvailabilityDiagnostic(
                reason=ToolUnavailableReason.UNSUPPORTED_SIGNAL,
                message="Unsupported availability expression",
            )
        ]
    return _evaluate_expression(expression, ctx)


def _sanitize_availability_expression(
    availability: ToolAvailabilityExpression,
) -> ToolAvailabilityExpression | None:
    """Validate/normalize a tool availability expression, returning None if malformed."""
    # If it has a signal, it's a leaf — valid
    if availability.signal is not None:
        return availability
    # If it has allOf or anyOf, it's a compound — valid
    if availability.all_of is not None or availability.any_of is not None:
        return availability
    return None
