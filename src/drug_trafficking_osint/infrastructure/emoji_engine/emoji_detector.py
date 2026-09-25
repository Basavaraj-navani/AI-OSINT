"""
Emoji Intelligence Detector.
"""

from __future__ import annotations

from time import perf_counter

from drug_trafficking_osint.infrastructure.emoji_engine.dictionary_loader import (
    DictionaryLoader,
)
from drug_trafficking_osint.infrastructure.emoji_engine.models import (
    EmojiAnalysisResult,
    EmojiMatch,
)


class EmojiDetector:
    """
    Detect drug-related emojis in raw text.
    """

    def __init__(self) -> None:
        """
        Load the emoji dictionary once.
        """
        self._dictionary = tuple(DictionaryLoader().load())

    def detect(self, text: str) -> EmojiAnalysisResult:
        """
        Detect all configured emojis within the supplied text.

        Args:
            text: Raw text to inspect.

        Returns:
            EmojiAnalysisResult containing every detected emoji.
        """

        started_at = perf_counter()

        matches: list[EmojiMatch] = []
        dictionary = self._dictionary

        for entry in dictionary:
            start = text.find(entry.emoji)

            while start != -1:
                matches.append(
                    EmojiMatch(
                        emoji=entry.emoji,
                        canonical_name=entry.canonical_name,
                        confidence=1.0,
                        start_index=start,
                        end_index=start + len(entry.emoji),
                    )
                )

                start = text.find(entry.emoji, start + len(entry.emoji))

        elapsed = perf_counter() - started_at

        return EmojiAnalysisResult(
            matches=tuple(matches),
            processing_time=elapsed,
        )
