"""
Core models shared across the intelligence pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Entity:
    """
    Named entity extracted from text.
    """

    text: str
    label: str
    start: int
    end: int


@dataclass(slots=True)
class ClassificationResult:
    """
    AI classifier output.
    """

    label: str
    confidence: float


@dataclass(slots=True)
class IntelligenceResult:
    """
    Complete intelligence analysis.
    """

    original_text: str
    processed_text: str

    slang_score: float
    emoji_score: float
    classifier_score: float
    ner_score: float

    risk_score: float = 0.0
    risk_label: str = "LOW"

    entities: list[Entity] = field(default_factory=lambda: [])

    classification: ClassificationResult | None = None
