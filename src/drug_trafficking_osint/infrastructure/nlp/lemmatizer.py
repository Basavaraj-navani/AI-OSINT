"""
Conservative rule-based lemmatization adapter.
"""

from __future__ import annotations


class RuleBasedLemmatizer:
    """
    Apply intentionally small English inflection rules without external models.
    """

    def lemmatize(
        self,
        tokens: tuple[str, ...],
        language: str,
        *,
        enabled: bool,
    ) -> tuple[str, ...]:
        """
        Return a stable token tuple after optional language-aware lemmatization.

        Only English is transformed because applying English morphology to other
        languages would silently corrupt terms. Other languages pass through.
        """
        if not enabled or language != "en":
            return tokens

        return tuple(self._lemmatize_english(token) for token in tokens)

    @staticmethod
    def _lemmatize_english(token: str) -> str:
        """
        Apply a very small set of English stemming rules.
        """

        if len(token) > 4 and token.endswith("ies"):
            return f"{token[:-3]}y"

        if len(token) > 5 and token.endswith("ing"):
            stem = token[:-3]
            if len(stem) > 2 and stem[-1] == stem[-2]:
                stem = stem[:-1]
            return stem

        if len(token) > 4 and token.endswith("ed"):
            stem = token[:-2]
            if len(stem) > 2 and stem[-1] == stem[-2]:
                stem = stem[:-1]
            return stem

        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            return token[:-1]

        return token
