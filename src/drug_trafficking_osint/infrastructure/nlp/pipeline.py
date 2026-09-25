"""Configurable orchestration of the reusable NLP preprocessing stages."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType
from typing import TypeVar

from drug_trafficking_osint.infrastructure.nlp.cleaner import TextCleaner
from drug_trafficking_osint.infrastructure.nlp.constants import (
    DEFAULT_MAX_TEXT_LENGTH,
    DEFAULT_MIN_TEXT_LENGTH,
    DEFAULT_PIPELINE_VERSION,
    DEFAULT_SUPPORTED_LANGUAGES,
)
from drug_trafficking_osint.infrastructure.nlp.exceptions import (
    EmptyTextError,
    InvalidConfigurationError,
    TextLengthError,
    UnsupportedLanguageError,
)
from drug_trafficking_osint.infrastructure.nlp.language_detector import HeuristicLanguageDetector
from drug_trafficking_osint.infrastructure.nlp.lemmatizer import RuleBasedLemmatizer
from drug_trafficking_osint.infrastructure.nlp.normalizer import TextNormalizer
from drug_trafficking_osint.infrastructure.nlp.stopwords import StopwordFilter
from drug_trafficking_osint.infrastructure.nlp.tokenizer import RegexTokenizer
from drug_trafficking_osint.infrastructure.nlp.utils import read_bool, read_csv, read_positive_int

_Result = TypeVar("_Result")


@dataclass(frozen=True, slots=True)
class PreprocessingConfig:
    """Immutable options controlling the preprocessing pipeline.

    Use :meth:`from_environment` to read ``OSINT_NLP_*`` settings. Every option
    is injectable directly for deterministic tests and specialized consumers.
    """

    min_text_length: int = DEFAULT_MIN_TEXT_LENGTH
    max_text_length: int = DEFAULT_MAX_TEXT_LENGTH
    remove_html: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    lowercase: bool = True
    normalize_unicode: bool = True
    normalize_mentions: bool = True
    normalize_usernames: bool = True
    remove_punctuation: bool = True
    remove_numbers: bool = False
    remove_stopwords: bool = True
    lemmatize: bool = True
    reject_unsupported_languages: bool = True
    supported_languages: tuple[str, ...] = DEFAULT_SUPPORTED_LANGUAGES
    pipeline_version: str = DEFAULT_PIPELINE_VERSION

    def __post_init__(self) -> None:
        """Validate cross-field invariants at construction time."""
        if self.min_text_length > self.max_text_length:
            raise InvalidConfigurationError("min_text_length cannot exceed max_text_length")
        if not self.supported_languages:
            raise InvalidConfigurationError("supported_languages must not be empty")
        if not self.pipeline_version.strip():
            raise InvalidConfigurationError("pipeline_version must not be empty")

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> PreprocessingConfig:
        """Build configuration from process environment without loading secret files.

        Supported values include ``OSINT_NLP_MAX_TEXT_LENGTH``,
        ``OSINT_NLP_REMOVE_URLS``, and other field names upper-cased with the
        ``OSINT_NLP_`` prefix. Boolean values accept true/false, yes/no, on/off,
        or 1/0; supported languages are comma-separated ISO-639-1 codes.
        """
        values = os.environ if environ is None else environ
        return cls(
            min_text_length=read_positive_int(
                values, "OSINT_NLP_MIN_TEXT_LENGTH", DEFAULT_MIN_TEXT_LENGTH
            ),
            max_text_length=read_positive_int(
                values, "OSINT_NLP_MAX_TEXT_LENGTH", DEFAULT_MAX_TEXT_LENGTH
            ),
            remove_html=read_bool(values, "OSINT_NLP_REMOVE_HTML", True),
            remove_urls=read_bool(values, "OSINT_NLP_REMOVE_URLS", True),
            remove_emails=read_bool(values, "OSINT_NLP_REMOVE_EMAILS", True),
            lowercase=read_bool(values, "OSINT_NLP_LOWERCASE", True),
            normalize_unicode=read_bool(values, "OSINT_NLP_NORMALIZE_UNICODE", True),
            normalize_mentions=read_bool(values, "OSINT_NLP_NORMALIZE_MENTIONS", True),
            normalize_usernames=read_bool(values, "OSINT_NLP_NORMALIZE_USERNAMES", True),
            remove_punctuation=read_bool(values, "OSINT_NLP_REMOVE_PUNCTUATION", True),
            remove_numbers=read_bool(values, "OSINT_NLP_REMOVE_NUMBERS", False),
            remove_stopwords=read_bool(values, "OSINT_NLP_REMOVE_STOPWORDS", True),
            lemmatize=read_bool(values, "OSINT_NLP_LEMMATIZE", True),
            reject_unsupported_languages=read_bool(
                values, "OSINT_NLP_REJECT_UNSUPPORTED_LANGUAGES", True
            ),
            supported_languages=read_csv(
                values, "OSINT_NLP_SUPPORTED_LANGUAGES", DEFAULT_SUPPORTED_LANGUAGES
            ),
            pipeline_version=values.get(
                "OSINT_NLP_PIPELINE_VERSION", DEFAULT_PIPELINE_VERSION
            ).strip(),
        )


@dataclass(frozen=True, slots=True)
class ProcessedText:
    """Immutable output produced by :class:`PreprocessingPipeline`.

    Attributes:
        original_text: Caller-provided text, retained for traceability.
        cleaned_text: Text after artifact and noise removal.
        normalized_text: Canonical lexical form used for tokenization.
        tokens: Final token sequence after filtering and lemmatization.
        language: Detected ISO-639-1 language code or ``unknown`` when allowed.
        processing_time: Whole-pipeline wall-clock duration in seconds.
        pipeline_version: Version of preprocessing rules used for the result.
        metadata: Immutable stage timings and token counts for observability.
    """

    original_text: str
    cleaned_text: str
    normalized_text: str
    tokens: tuple[str, ...]
    language: str
    processing_time: float
    pipeline_version: str
    metadata: Mapping[str, object] = field(default_factory=dict)


class PreprocessingPipeline:
    """Coordinate validated text preprocessing with constructor-injected stages.

    Example:
        >>> result = PreprocessingPipeline().process("<p>Hello @analyst</p>")
        >>> result.tokens
        ('hello', 'mention')
    """

    def __init__(
        self,
        config: PreprocessingConfig | None = None,
        *,
        cleaner: TextCleaner | None = None,
        normalizer: TextNormalizer | None = None,
        tokenizer: RegexTokenizer | None = None,
        stopword_filter: StopwordFilter | None = None,
        lemmatizer: RuleBasedLemmatizer | None = None,
        language_detector: HeuristicLanguageDetector | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Create the reusable pipeline with optional explicit stage dependencies."""
        self._config = config or PreprocessingConfig.from_environment()
        self._cleaner = cleaner or TextCleaner()
        self._normalizer = normalizer or TextNormalizer()
        self._tokenizer = tokenizer or RegexTokenizer()
        self._stopword_filter = stopword_filter or StopwordFilter()
        self._lemmatizer = lemmatizer or RuleBasedLemmatizer()
        self._language_detector = language_detector or HeuristicLanguageDetector()
        self._logger = logger or logging.getLogger("drug-trafficking-osint.nlp")

    def process(self, raw_text: str, *, language_hint: str | None = None) -> ProcessedText:
        """Process one raw text value into a reusable, immutable result.

        Args:
            raw_text: Non-empty textual OSINT content no longer than configured limit.
            language_hint: Optional supported ISO-639-1 code that bypasses detection.

        Raises:
            EmptyTextError: If input is ``None``, not a string, or becomes empty.
            TextLengthError: If raw input violates configured length boundaries.
            UnsupportedLanguageError: If policy rejects the resolved language.
        """
        started_at = perf_counter()
        self._validate_input(raw_text)
        stage_timings: dict[str, float] = {}
        cleaned_text = self._run_stage(
            "clean",
            stage_timings,
            lambda: self._cleaner.clean(
                raw_text,
                remove_html=self._config.remove_html,
                remove_urls=self._config.remove_urls,
                remove_emails=self._config.remove_emails,
            ),
        )
        self._validate_non_empty(cleaned_text, "cleaning")
        normalized_text = self._run_stage(
            "normalize",
            stage_timings,
            lambda: self._normalizer.normalize(
                cleaned_text,
                lowercase=self._config.lowercase,
                normalize_unicode=self._config.normalize_unicode,
                normalize_mentions=self._config.normalize_mentions,
                normalize_usernames=self._config.normalize_usernames,
                remove_punctuation=self._config.remove_punctuation,
                remove_numbers=self._config.remove_numbers,
            ),
        )
        self._validate_non_empty(normalized_text, "normalization")
        filter_language = (
            language_hint.lower()
            if language_hint
            else self._language_detector.detect(normalized_text, self._config.supported_languages)
        )
        tokens = self._run_stage(
            "tokenize", stage_timings, lambda: self._tokenizer.tokenize(normalized_text)
        )
        tokens = self._run_stage(
            "stopword_removal",
            stage_timings,
            lambda: self._stopword_filter.remove(
                tokens, filter_language, enabled=self._config.remove_stopwords
            ),
        )
        tokens = self._run_stage(
            "lemmatize",
            stage_timings,
            lambda: self._lemmatizer.lemmatize(
                tokens, filter_language, enabled=self._config.lemmatize
            ),
        )
        language = self._resolve_language(normalized_text, language_hint, stage_timings)
        elapsed = perf_counter() - started_at
        metadata = MappingProxyType(
            {"stage_timings_seconds": MappingProxyType(stage_timings), "token_count": len(tokens)}
        )
        self._logger.info(
            "nlp_pipeline_completed",
            extra={
                "language": language,
                "processing_time_seconds": elapsed,
                "token_count": len(tokens),
            },
        )
        return ProcessedText(
            original_text=raw_text,
            cleaned_text=cleaned_text,
            normalized_text=normalized_text,
            tokens=tokens,
            language=language,
            processing_time=elapsed,
            pipeline_version=self._config.pipeline_version,
            metadata=metadata,
        )

    def _validate_input(self, raw_text: str) -> None:
        if not isinstance(raw_text, str) or not raw_text.strip():
            self._logger.warning("nlp_invalid_input", extra={"reason": "empty_or_non_string"})
            raise EmptyTextError("raw_text must be a non-empty string")
        length = len(raw_text)
        if not self._config.min_text_length <= length <= self._config.max_text_length:
            self._logger.warning("nlp_invalid_input", extra={"reason": "length", "length": length})
            raise TextLengthError(
                f"raw_text length must be between {self._config.min_text_length} "
                f"and {self._config.max_text_length}"
            )

    def _validate_non_empty(self, text: str, stage: str) -> None:
        if not text:
            self._logger.warning(
                "nlp_invalid_output", extra={"stage": stage, "reason": "empty_text"}
            )
            raise EmptyTextError(f"text is empty after {stage}")

    def _resolve_language(
        self, normalized_text: str, language_hint: str | None, stage_timings: dict[str, float]
    ) -> str:
        language = (
            language_hint.lower()
            if language_hint
            else self._run_stage(
                "language_detection",
                stage_timings,
                lambda: self._language_detector.detect(
                    normalized_text, self._config.supported_languages
                ),
            )
        )
        if language not in self._config.supported_languages:
            self._logger.warning("nlp_unsupported_language", extra={"language": language})
            if self._config.reject_unsupported_languages:
                raise UnsupportedLanguageError(f"Unsupported language: {language}")
        return language

    def _run_stage(
        self, name: str, timings: dict[str, float], action: Callable[[], _Result]
    ) -> _Result:
        started_at = perf_counter()
        try:
            value = action()
        except Exception:
            self._logger.exception("nlp_stage_failed", extra={"stage": name})
            raise
        elapsed = perf_counter() - started_at
        timings[name] = elapsed
        self._logger.info(
            "nlp_stage_completed", extra={"stage": name, "processing_time_seconds": elapsed}
        )
        return value
