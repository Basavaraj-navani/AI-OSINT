"""Unicode and lexical normalization stage."""

from __future__ import annotations

import unicodedata

from drug_trafficking_osint.infrastructure.nlp.constants import (
    MENTION_PATTERN,
    NUMBER_PATTERN,
    PUNCTUATION_PATTERN,
    USERNAME_PATTERN,
    WHITESPACE_PATTERN,
)


class TextNormalizer:
    """Apply deterministic normalization while preserving configurable semantics."""

    def normalize(
        self,
        text: str,
        *,
        lowercase: bool,
        normalize_unicode: bool,
        normalize_mentions: bool,
        normalize_usernames: bool,
        remove_punctuation: bool,
        remove_numbers: bool,
    ) -> str:
        """Normalize text into a stable representation for downstream consumers.

        ``@handles`` become ``mention`` and Reddit-style ``u/handles`` become
        ``username`` when their corresponding normalization option is enabled.
        """
        normalized = unicodedata.normalize("NFKC", text) if normalize_unicode else text
        if normalize_usernames:
            normalized = USERNAME_PATTERN.sub(" username ", normalized)
        if normalize_mentions:
            normalized = MENTION_PATTERN.sub(" mention ", normalized)
        if lowercase:
            normalized = normalized.lower()
        if remove_punctuation:
            normalized = PUNCTUATION_PATTERN.sub(" ", normalized)
        if remove_numbers:
            normalized = NUMBER_PATTERN.sub(" ", normalized)
        return WHITESPACE_PATTERN.sub(" ", normalized).strip()
