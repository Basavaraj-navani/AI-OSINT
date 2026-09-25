"""
Tests the AI classifier.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.classifier.classifier import (
    AIClassifier,
)


def main() -> None:
    classifier = AIClassifier()

    samples = [
        "I love playing football with my friends.",
        "Rahul will deliver ❄️ and snow to Bangalore tomorrow.",
        "Let's meet for coffee this evening.",
        "The package will be delivered through Telegram.",
    ]

    print("=" * 70)
    print("AI CLASSIFIER TEST")
    print("=" * 70)

    for index, text in enumerate(samples, start=1):
        result = classifier.predict(text)

        print(f"\nSample {index}")
        print("-" * 70)
        print(f"Text       : {text}")
        print(f"Prediction : {result.label}")
        print(f"Confidence : {result.confidence:.4f}")


if __name__ == "__main__":
    main()
