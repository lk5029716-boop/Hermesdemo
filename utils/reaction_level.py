"""
reaction_level.py — Reaction/emoji level configuration.

Adapted from OpenClaw src/utils/reaction-level.ts.

Maps reaction names to numeric levels and categories.
Useful for messaging platforms that support reactions/emojis.

Hermes gateway platforms (Telegram, Discord, Slack) all support
reactions. This provides a unified abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReactionCategory(str, Enum):
    """Category of reaction."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FUNNY = "funny"
    ALERT = "alert"


# Default reaction level mapping
DEFAULT_REACTION_LEVELS: dict[str, int] = {
    # Positive
    "👍": 1, "thumbsup": 1, "like": 1,
    "❤️": 2, "heart": 2, "love": 2,
    "🎉": 3, "party": 3, "celebrate": 3,
    "🔥": 4, "fire": 4,
    "💯": 5, "100": 5,
    # Negative
    "👎": -1, "thumbsdown": -1, "dislike": -1,
    "😢": -2, "cry": -2, "sad": -2,
    "😡": -3, "angry": -3,
    # Neutral
    "🤔": 0, "thinking": 0,
    "👀": 0, "eyes": 0,
    "✅": 0, "check": 0,
    # Funny
    "😂": 1, "laugh": 1,
    "💀": 2, "dead": 2,
    # Alert
    "⚠️": 1, "warning": 1,
    "🚨": 2, "alert": 2,
    "❌": -1, "x": -1, "cross": -1,
}


@dataclass
class ReactionLevel:
    """A reaction with its numeric level and category."""
    name: str
    level: int
    category: ReactionCategory
    emoji: str | None = None


def get_reaction_level(name_or_emoji: str) -> ReactionLevel:
    """
    Get the level and category for a reaction.

    Args:
        name_or_emoji: Reaction name ("like") or emoji ("👍")

    Returns:
        ReactionLevel with level and category
    """
    normalized = name_or_emoji.strip().lower()
    level = DEFAULT_REACTION_LEVELS.get(name_or_emoji, 0)
    if level == 0:
        level = DEFAULT_REACTION_LEVELS.get(normalized, 0)

    if level > 0:
        category = ReactionCategory.POSITIVE
    elif level < 0:
        category = ReactionCategory.NEGATIVE
    else:
        category = ReactionCategory.NEUTRAL

    # Check for special categories
    if name_or_emoji in ("😂", "💀", "laugh", "dead"):
        category = ReactionCategory.FUNNY
    elif name_or_emoji in ("⚠️", "🚨", "warning", "alert"):
        category = ReactionCategory.ALERT

    return ReactionLevel(
        name=normalized,
        level=level,
        category=category,
        emoji=name_or_emoji if len(name_or_emoji) <= 4 else None,
    )


def emoji_from_level(level: int) -> str:
    """Get a default emoji for a reaction level."""
    mapping = {
        -3: "😡", -2: "😢", -1: "👎",
        0: "🤔",
        1: "👍", 2: "❤️", 3: "🎉", 4: "🔥", 5: "💯",
    }
    return mapping.get(level, "🤔")


def should_highlight(level: int, threshold: int = 2) -> bool:
    """Check if a reaction level should be highlighted/displayed."""
    return abs(level) >= threshold
