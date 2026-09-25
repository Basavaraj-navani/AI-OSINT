"""
Tests the Named Entity Recognition (NER) detector.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.ner_engine.ner_detector import (
    NERDetector,
)


def main() -> None:
    detector = NERDetector()

    text = "Rahul will deliver ❄️ to Bangalore on Friday for ₹5000 using Telegram."

    result = detector.detect(text)

    print("=" * 60)
    print("NER DETECTOR TEST")
    print("=" * 60)

    print(f"\nInput:\n{text}")

    print("\nDetected Entities")
    print("-" * 60)

    if not result.entities:
        print("No entities detected.")
        return

    for entity in result.entities:
        print(f"{entity.text:<20}{entity.label:<15}[{entity.start_char}, {entity.end_char}]")


if __name__ == "__main__":
    main()
