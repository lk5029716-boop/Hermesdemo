"""Pluggable truncation strategies for conversation context management.

Provides a clean ABC interface for different truncation approaches.
Each strategy is self-contained and independently testable.

Usage:
    from agent.truncation_strategies import get_strategy
    strategy = get_strategy("sliding_window")
    truncated_messages = strategy.truncate(messages, budget_tokens=4000)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TruncationResult:
    """Result of a truncation operation."""

    def __init__(
        self,
        messages: List[Dict[str, Any]],
        tokens_before: int,
        tokens_after: int,
        strategy_name: str,
    ):
        self.messages = messages
        self.tokens_before = tokens_before
        self.tokens_after = tokens_after
        self.strategy_name = strategy_name

    @property
    def tokens_saved(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)

    @property
    def did_truncate(self) -> bool:
        return self.tokens_after < self.tokens_before


class TruncationStrategy(ABC):
    """Base class for all truncation strategies."""

    name: str = "base"

    @abstractmethod
    def truncate(
        self,
        messages: List[Dict[str, Any]],
        budget_tokens: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> TruncationResult:
        """Truncate messages to fit within budget_tokens.

        Args:
            messages: List of conversation messages
            budget_tokens: Maximum tokens allowed
            config: Optional strategy-specific config

        Returns:
            TruncationResult with truncated messages
        """
        ...


class NoTruncationStrategy(TruncationStrategy):
    """Keep all messages, do nothing."""

    name = "none"

    def truncate(
        self,
        messages: List[Dict[str, Any]],
        budget_tokens: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> TruncationResult:
        from agent.model_metadata import estimate_messages_tokens_rough

        tokens = estimate_messages_tokens_rough(messages)
        return TruncationResult(
            messages=messages,
            tokens_before=tokens,
            tokens_after=tokens,
            strategy_name=self.name,
        )


class SlidingWindowStrategy(TruncationStrategy):
    """Keep the last N messages, drop oldest ones.

    Config options:
        keep_last: Number of messages to keep (default: 40)
        keep_first: Number of messages to always keep from the start (default: 3)
                   Usually the system prompt + first exchanges
    """

    name = "sliding_window"

    def truncate(
        self,
        messages: List[Dict[str, Any]],
        budget_tokens: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> TruncationResult:
        from agent.model_metadata import estimate_messages_tokens_rough

        cfg = config or {}
        keep_last = int(cfg.get("keep_last", 40))
        keep_first = int(cfg.get("keep_first", 3))

        tokens_before = estimate_messages_tokens_rough(messages)

        if len(messages) <= keep_last:
            return TruncationResult(
                messages=messages,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                strategy_name=self.name,
            )

        # Always keep first N messages (system prompt etc.)
        head = messages[:keep_first]

        # Keep last N messages
        tail = messages[-keep_last:]

        # Add a marker message between head and tail
        dropped_count = len(messages) - keep_first - keep_last
        marker = {
            "role": "system",
            "content": f"[... {dropped_count} earlier messages truncated by sliding window ...]",
        }

        result_messages = head + marker + tail
        tokens_after = estimate_messages_tokens_rough(result_messages)

        logger.info(
            "SlidingWindow: %d → %d messages (%d → %d tokens, saved %d)",
            len(messages),
            len(result_messages),
            tokens_before,
            tokens_after,
            tokens_before - tokens_after,
        )

        return TruncationResult(
            messages=result_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            strategy_name=self.name,
        )


class SummarizationStrategy(TruncationStrategy):
    """Use LLM summarization (wraps existing ContextCompressor).

    This is what Hermes already does with /compress.
    This strategy makes it pluggable.

    Config options:
        compression_threshold: When to trigger (0.0-1.0, default: 0.50)
        compression_target_ratio: Target ratio after compression (default: 0.20)
        compression_protect_last_n: Number of recent messages to protect (default: 20)
    """

    name = "summarization"

    def truncate(
        self,
        messages: List[Dict[str, Any]],
        budget_tokens: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> TruncationResult:
        from agent.model_metadata import estimate_messages_tokens_rough
        from agent.context_compressor import ContextCompressor

        tokens_before = estimate_messages_tokens_rough(messages)

        # If already under budget, no need to summarize
        if tokens_before <= budget_tokens:
            return TruncationResult(
                messages=messages,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                strategy_name=self.name,
            )

        cfg = config or {}

        # Read compression settings from config or use defaults
        threshold = float(cfg.get("compression_threshold", 0.50))
        target_ratio = float(cfg.get("compression_target_ratio", 0.20))
        protect_last = int(cfg.get("compression_protect_last_n", 20))

        # Get model context length
        from agent.model_metadata import MINIMUM_CONTEXT_LENGTH
        from hermes_cli import cli

        try:
            current_model = cli.get_current_model()
            model_context_length = MINIMUM_CONTEXT_LENGTH
        except Exception:
            model_context_length = MINIMUM_CONTEXT_LENGTH

        # Create compressor and compress
        compressor = ContextCompressor(
            threshold=threshold,
            target_ratio=target_ratio,
            protect_last_n=protect_last,
            context_length=model_context_length,
        )

        try:
            result_messages = compressor.compress(messages)
            tokens_after = estimate_messages_tokens_rough(result_messages)

            logger.info(
                "Summarization: %d → %d messages (%d → %d tokens, saved %d)",
                len(messages),
                len(result_messages),
                tokens_before,
                tokens_after,
                tokens_before - tokens_after,
            )

            return TruncationResult(
                messages=result_messages,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                strategy_name=self.name,
            )
        except Exception as e:
            logger.error("Summarization failed: %s", e)
            # Fallback: return original messages
            return TruncationResult(
                messages=messages,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                strategy_name=self.name,
            )


# Registry of all available strategies
_STRATEGIES = {
    "none": NoTruncationStrategy(),
    "sliding_window": SlidingWindowStrategy(),
    "summarization": SummarizationStrategy(),
}


def get_strategy(name: str) -> TruncationStrategy:
    """Get a truncation strategy by name.

    Args:
        name: Strategy name ('none', 'sliding_window', 'summarization')

    Returns:
        TruncationStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    if name not in _STRATEGIES:
        available = ", ".join(sorted(_STRATEGIES.keys()))
        raise ValueError(
            f"Unknown truncation strategy '{name}'. Available: {available}"
        )
    return _STRATEGIES[name]


def list_strategies() -> List[str]:
    """Return list of available strategy names."""
    return sorted(_STRATEGIES.keys())


def register_strategy(name: str, strategy: TruncationStrategy) -> None:
    """Register a custom truncation strategy.

    Args:
        name: Strategy name
        strategy: TruncationStrategy instance
    """
    _STRATEGIES[name] = strategy
    logger.info("Registered custom truncation strategy: %s", name)
