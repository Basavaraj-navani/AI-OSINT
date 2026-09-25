"""
Named Entity Recognition (NER) Detector.
"""

from __future__ import annotations

from collections.abc import Iterable
from time import perf_counter
from typing import Protocol, TypedDict, cast


class _SpaCyEntity(Protocol):
    text: str
    label_: str
    start_char: int
    end_char: int


class _SpaCyDocument(Protocol):
    ents: Iterable[_SpaCyEntity]


class _SpaCyLanguage(Protocol):
    def __call__(self, text: str) -> _SpaCyDocument: ...


class _SpaCyModule(Protocol):
    def load(self, model_name: str) -> _SpaCyLanguage: ...


class _EntityData(TypedDict):
    text: str
    label: str
    start: int
    end: int


class _NERResult(TypedDict):
    entities: tuple[_EntityData, ...]
    processing_time: float


_spacy: _SpaCyModule | None
try:
    import spacy

    _spacy = cast("_SpaCyModule", spacy)
except ImportError:
    _spacy = None


class NERDetector:
    """
    Performs Named Entity Recognition using spaCy when available.
    """

    def __init__(self) -> None:
        self._nlp: _SpaCyLanguage | None = None

        if _spacy is not None:
            try:
                self._nlp = _spacy.load("en_core_web_sm")
            except OSError:
                self._nlp = None

    def detect(self, text: str) -> _NERResult:
        """
        Detect named entities in text.

        Args:
            text: Input text.

        Returns:
            Dictionary containing detected entities and processing time.
        """

        started_at = perf_counter()

        entities: list[_EntityData] = []

        if self._nlp is not None:
            doc = self._nlp(text)

            for entity in doc.ents:
                entities.append(
                    {
                        "text": entity.text,
                        "label": entity.label_,
                        "start": entity.start_char,
                        "end": entity.end_char,
                    }
                )

        elapsed = perf_counter() - started_at

        return {
            "entities": tuple(entities),
            "processing_time": elapsed,
        }
