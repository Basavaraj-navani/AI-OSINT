"""
Tests for the Risk Calculator.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.risk_engine.risk_calculator import (
    RiskCalculator,
)


def main() -> None:
    """
    Test the Risk Calculator.
    """

    calculator = RiskCalculator()

    result = calculator.calculate(
        classifier_score=0.95,
        slang_score=1.00,
        emoji_score=1.00,
        ner_score=0.80,
    )

    print("Risk Score :", result.score)
    print("Risk Label :", result.label)


if __name__ == "__main__":
    main()
