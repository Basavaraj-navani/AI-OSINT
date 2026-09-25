"""
Data models for the Intelligence Coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass

from drug_trafficking_osint.infrastructure.classifier.models import (
    ClassificationResult,
)
from drug_trafficking_osint.infrastructure.emoji_engine.models import (
    EmojiAnalysisResult,
)
from drug_trafficking_osint.infrastructure.ner_engine.models import (
    NERAnalysisResult,
)
from drug_trafficking_osint.infrastructure.risk_engine.models import (
    RiskScore,
)
from drug_trafficking_osint.infrastructure.slang_engine.models import (
    DrugAnalysisResult,
)


@dataclass(frozen=True, slots=True)
class IntelligenceResult:
    """
    Combined intelligence produced by all detectors.
    """

    original_text: str

    slang_result: DrugAnalysisResult

    emoji_result: EmojiAnalysisResult

    ner_result: NERAnalysisResult

    classifier_result: ClassificationResult

    risk_result: RiskScore
