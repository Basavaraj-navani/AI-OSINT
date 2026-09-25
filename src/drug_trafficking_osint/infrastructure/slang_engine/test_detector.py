from drug_trafficking_osint.infrastructure.nlp.pipeline import (
    PreprocessingPipeline,
)
from drug_trafficking_osint.infrastructure.slang_engine.slang_detector import (
    SlangDetector,
)


def main() -> None:
    text = "Need snow tonight."

    pipeline = PreprocessingPipeline()
    processed = pipeline.process(text)

    detector = SlangDetector()

    result = detector.detect(processed)

    print("\nDetected Matches")
    print("----------------")

    if not result.matches:
        print("No drug slang detected.")
        return

    for match in result.matches:
        print(f"Matched Text   : {match.matched_text}")
        print(f"Canonical Name: {match.canonical_name}")
        print(f"Match Type     : {match.match_type}")
        print(f"Confidence     : {match.confidence}")
        print(f"Token Index    : {match.start_index}")
        print()


if __name__ == "__main__":
    main()
