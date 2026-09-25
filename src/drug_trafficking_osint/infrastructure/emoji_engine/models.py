"""
Data models for the Emoji Intelligence Engine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmojiEntry:
    """
    Represents one emoji intelligence entry.
    """

    emoji: str
    canonical_name: str
    category: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmojiMatch:
    """
    Represents one detected emoji.
    """

    emoji: str
    canonical_name: str
    confidence: float
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class EmojiAnalysisResult:
    """
    Output of the emoji detector.
    """

    matches: tuple[EmojiMatch, ...]
    processing_time: float
