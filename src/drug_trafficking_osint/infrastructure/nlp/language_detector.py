"""Transparent heuristic language detection for supported Latin-script text."""

from __future__ import annotations

import unicodedata

from drug_trafficking_osint.infrastructure.nlp.constants import LANGUAGE_STOPWORDS


class HeuristicLanguageDetector:
    """Detect configured languages using stopword evidence and Unicode scripts."""

    def detect(self, text: str, supported_languages: tuple[str, ...]) -> str:
        """Return the best supported language or ``unknown`` for unsupported scripts.

        Latin text without enough stopword evidence defaults to English so short
        operational messages remain usable. Non-Latin text is never guessed.
        """
        if self._contains_non_latin_letters(text):
            return "unknown"
        words = {word.casefold() for word in text.split()}
        scores = {
            language: len(words.intersection(LANGUAGE_STOPWORDS.get(language, frozenset())))
            for language in supported_languages
        }
        best_language = max(scores, key=scores.__getitem__, default="en")
        if scores.get(best_language, 0) > 0:
            return best_language
        return "en" if "en" in supported_languages else "unknown"

    @staticmethod
    def _contains_non_latin_letters(text: str) -> bool:
        for character in text:
            if character.isalpha() and "LATIN" not in unicodedata.name(character, ""):
                return True
        return False
