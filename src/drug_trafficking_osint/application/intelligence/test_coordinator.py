"""
Tests the Intelligence Coordinator.
"""

from __future__ import annotations

from drug_trafficking_osint.application.intelligence.coordinator import (
    IntelligenceCoordinator,
)


def main() -> None:
    coordinator = IntelligenceCoordinator()

    text = "Rahul will deliver ❄️ and snow to Bangalore on Friday for ₹5000 using Telegram."

    result = coordinator.analyze(text)

    print("=" * 70)
    print("INTELLIGENCE COORDINATOR TEST")
    print("=" * 70)

    print(f"\nOriginal Text:\n{result.original_text}")

    print("\nSlang Intelligence")
    print("-" * 70)

    if result.slang_result.matches:
        for slang_match in result.slang_result.matches:
            print(
                f"{slang_match.matched_text:<15}{slang_match.canonical_name:<15}"
                f"{slang_match.confidence:.2f}"
            )
    else:
        print("No slang detected.")

    print("\nEmoji Intelligence")
    print("-" * 70)

    if result.emoji_result.matches:
        for emoji_match in result.emoji_result.matches:
            print(
                f"{emoji_match.emoji:<15}{emoji_match.canonical_name:<15}"
                f"{emoji_match.confidence:.2f}"
            )
    else:
        print("No emojis detected.")

    print("\nNamed Entities")
    print("-" * 70)

    if result.ner_result.entities:
        for entity in result.ner_result.entities:
            print(f"{entity.text:<20}{entity.label:<15}[{entity.start_char}, {entity.end_char}]")
    else:
        print("No entities detected.")


if __name__ == "__main__":
    main()
