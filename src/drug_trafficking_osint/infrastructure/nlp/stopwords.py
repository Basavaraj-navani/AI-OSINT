"""
Language-specific stopword filtering adapter.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.nlp.constants import (
    LANGUAGE_STOPWORDS,
)


class StopwordFilter:
    """
    Remove a conservative built-in stopword set.
    """

    def remove(
        self,
        tokens: tuple[str, ...],
        language: str,
        *,
        enabled: bool,
    ) -> tuple[str, ...]:
        """
        Return tokens with configured language stopwords removed.

        Unknown languages retain their tokens.
        """

        if not enabled:
            return tokens

        stopwords = LANGUAGE_STOPWORDS.get(language, frozenset())

        return tuple(token for token in tokens if token.casefold() not in stopwords)
