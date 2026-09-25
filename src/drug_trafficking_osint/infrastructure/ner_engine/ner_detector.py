"""
Named Entity Recognition (NER) detector using spaCy.
"""

from __future__ import annotations

import spacy
from spacy.language import Language

from drug_trafficking_osint.infrastructure.ner_engine.constants import (
    MODEL_NAME,
)
from drug_trafficking_osint.infrastructure.ner_engine.exceptions import (
    ModelLoadError,
)
from drug_trafficking_osint.infrastructure.ner_engine.models import (
    NamedEntity,
    NERAnalysisResult,
)


class NERDetector:
    """
    Detects named entities using spaCy.
    """

    def __init__(self) -> None:
        try:
            self.nlp: Language = spacy.load(MODEL_NAME)
        except OSError as exc:
            raise ModelLoadError(f"Unable to load spaCy model '{MODEL_NAME}'.") from exc

    def detect(self, text: str) -> NERAnalysisResult:
        """
        Detect all named entities in the given text.
        """
        doc = self.nlp(text)

        entities = tuple(
            NamedEntity(
                text=entity.text,
                label=entity.label_,
                start_char=entity.start_char,
                end_char=entity.end_char,
            )
            for entity in doc.ents
        )

        return NERAnalysisResult(
            entities=entities,
        )
