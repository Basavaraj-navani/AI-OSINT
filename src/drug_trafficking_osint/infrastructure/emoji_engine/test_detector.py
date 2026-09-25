from drug_trafficking_osint.infrastructure.emoji_engine.emoji_detector import (
    EmojiDetector,
)


def main() -> None:
    text = "Need ❄️ and 💊 tonight."

    detector = EmojiDetector()

    result = detector.detect(text)

    print("\nDetected Emojis")
    print("----------------")

    if not result.matches:
        print("No emojis detected.")
        return

    for match in result.matches:
        print(f"Emoji          : {match.emoji}")
        print(f"Drug           : {match.canonical_name}")
        print(f"Confidence     : {match.confidence}")
        print()


if __name__ == "__main__":
    main()
