"""
Data models for the Named Entity Recognition engine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NamedEntity:
    """
    Represents a detected named entity.
    """

    text: str
    label: str
    start_char: int
    end_char: int


@dataclass(frozen=True, slots=True)
class NERAnalysisResult:
    """
    Contains all entities detected in a text.
    """

    entities: tuple[NamedEntity, ...]
