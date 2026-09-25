"""
Drug Slang Detector.
"""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.nlp.pipeline import ProcessedText
from drug_trafficking_osint.infrastructure.slang_engine.constants import (
    EXACT_MATCH,
)
from drug_trafficking_osint.infrastructure.slang_engine.dictionary_loader import (
    DictionaryLoader,
)
from drug_trafficking_osint.infrastructure.slang_engine.models import (
    DrugAnalysisResult,
    DrugMatch,
)


class SlangDetector:
    """
    Detect drug-related slang terms from preprocessed text.
    """

    def __init__(self) -> None:
        """
        Load the slang dictionary once during initialization.
        """
        self._dictionary = tuple(DictionaryLoader().load())

    def detect(self, processed_text: ProcessedText) -> DrugAnalysisResult:
        """
        Detect known drug slang from NLP processed text.

        Args:
            processed_text: Output of the NLP preprocessing pipeline.

        Returns:
            DrugAnalysisResult containing all detected slang matches.
        """

        matches: list[DrugMatch] = []

        tokens = tuple(token.lower() for token in processed_text.tokens)

        for token_index, token in enumerate(tokens):
            for drug in self._dictionary:
                canonical_name = drug.canonical_name.lower()
                aliases = {alias.lower() for alias in drug.aliases}

                if token == canonical_name or token in aliases:
                    matches.append(
                        DrugMatch(
                            matched_text=token,
                            canonical_name=drug.canonical_name,
                            match_type=EXACT_MATCH,
                            confidence=1.0,
                            start_index=token_index,
                            end_index=token_index,
                        )
                    )

        return DrugAnalysisResult(
            matches=tuple(matches),
            processing_time=0.0,
        )
