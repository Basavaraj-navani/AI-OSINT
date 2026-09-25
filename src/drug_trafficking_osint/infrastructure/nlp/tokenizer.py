"""
Dependency-free tokenization adapter.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.nlp.constants import TOKEN_PATTERN


class RegexTokenizer:
    """
    Extract Unicode word tokens while retaining internal apostrophes
    and hyphens.
    """

    def tokenize(self, text: str) -> tuple[str, ...]:
        """
        Tokenize normalized text into an immutable tuple of tokens.

        Args:
            text: Normalized input text.

        Returns:
            A tuple containing all extracted tokens.
        """

        return tuple(TOKEN_PATTERN.findall(text))
