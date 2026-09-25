"""
Risk Calculator
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.risk_engine.constants import (
    CLASSIFIER_WEIGHT,
    EMOJI_WEIGHT,
    HIGH_RISK,
    HIGH_THRESHOLD,
    LOW_RISK,
    LOW_THRESHOLD,
    MEDIUM_RISK,
    MEDIUM_THRESHOLD,
    NER_WEIGHT,
    SLANG_WEIGHT,
)
from drug_trafficking_osint.infrastructure.risk_engine.models import RiskScore


class RiskCalculator:
    """
    Calculates the overall risk score.
    """

    def calculate(
        self,
        classifier_score: float,
        slang_score: float,
        emoji_score: float,
        ner_score: float,
    ) -> RiskScore:
        """
        Calculate the final weighted risk score.
        """

        score = (
            classifier_score * CLASSIFIER_WEIGHT
            + slang_score * SLANG_WEIGHT
            + emoji_score * EMOJI_WEIGHT
            + ner_score * NER_WEIGHT
        )

        if score >= HIGH_THRESHOLD:
            label = HIGH_RISK
        elif score >= MEDIUM_THRESHOLD:
            label = MEDIUM_RISK
        elif score >= LOW_THRESHOLD:
            label = LOW_RISK
        else:
            label = LOW_RISK

        return RiskScore(
            score=round(score, 3),
            label=label,
        )
