"""
Data models for the Drug Slang Intelligence Engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class DrugEntry:
    """
    Represents one drug entry loaded from the slang dictionary.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    hashtags: tuple[str, ...]
    category: str
    risk_weight: float


@dataclass(frozen=True, slots=True)
class DrugMatch:
    """
    Represents one detected drug-related match.
    """

    matched_text: str
    canonical_name: str
    match_type: str
    confidence: float
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class DrugAnalysisResult:
    """
    Output of the Drug Slang Intelligence Engine.
    """

    matches: tuple[DrugMatch, ...]
    processing_time: float
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
