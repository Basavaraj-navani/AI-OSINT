from __future__ import annotations

import logging

import pytest

from drug_trafficking_osint.infrastructure.nlp.cleaner import TextCleaner
from drug_trafficking_osint.infrastructure.nlp.constants import DEFAULT_SUPPORTED_LANGUAGES
from drug_trafficking_osint.infrastructure.nlp.exceptions import (
    EmptyTextError,
    InvalidConfigurationError,
    TextLengthError,
    UnsupportedLanguageError,
)
from drug_trafficking_osint.infrastructure.nlp.language_detector import HeuristicLanguageDetector
from drug_trafficking_osint.infrastructure.nlp.lemmatizer import RuleBasedLemmatizer
from drug_trafficking_osint.infrastructure.nlp.normalizer import TextNormalizer
from drug_trafficking_osint.infrastructure.nlp.pipeline import (
    PreprocessingConfig,
    PreprocessingPipeline,
)
from drug_trafficking_osint.infrastructure.nlp.stopwords import StopwordFilter
from drug_trafficking_osint.infrastructure.nlp.tokenizer import RegexTokenizer
from drug_trafficking_osint.infrastructure.nlp.utils import read_bool, read_csv, read_positive_int


def test_pipeline_processes_normal_osint_text() -> None:
    result = PreprocessingPipeline().process(
        "<article>Hello @Alice and /u/Bob! Visit https://example.org. "
        "Email tips@example.org.</article>"
    )

    assert result.original_text.startswith("<article>")
    assert "https" not in result.cleaned_text
    assert "tips@example.org" not in result.cleaned_text
    assert result.normalized_text == "hello mention and username visit email"
    assert result.tokens == ("hello", "mention", "username", "visit", "email")
    assert result.language == "en"
    assert result.processing_time >= 0
    assert result.metadata["token_count"] == 5


def test_pipeline_normalizes_unicode_whitespace_punctuation_and_numbers() -> None:
    pipeline = PreprocessingPipeline(
        PreprocessingConfig(remove_numbers=True, remove_stopwords=False, lemmatize=False)
    )
    result = pipeline.process("  CAF\uff25\u00a0\u00a0\tPrice: 123!!!  ")

    assert result.normalized_text == "cafe price"
    assert result.tokens == ("cafe", "price")


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("La información está en el canal", "es"),
        ("Le message est pour une équipe", "fr"),
        ("Der Hinweis ist mit dem Kanal", "de"),
        ("Uma mensagem para os grupos", "pt"),
    ],
)
def test_pipeline_detects_supported_languages(text: str, language: str) -> None:
    result = PreprocessingPipeline().process(text)
    assert result.language == language


def test_pipeline_accepts_supported_language_hint() -> None:
    result = PreprocessingPipeline().process("brief message", language_hint="es")
    assert result.language == "es"


@pytest.mark.parametrize("value", [None, "", " \t\n ", 7])
def test_pipeline_rejects_empty_or_non_string_input(value: object) -> None:
    with pytest.raises(EmptyTextError):
        PreprocessingPipeline().process(value)  # type: ignore[arg-type]


def test_pipeline_rejects_text_outside_length_policy() -> None:
    pipeline = PreprocessingPipeline(PreprocessingConfig(min_text_length=3, max_text_length=5))
    with pytest.raises(TextLengthError):
        pipeline.process("hi")
    with pytest.raises(TextLengthError):
        pipeline.process("toolong")


def test_pipeline_rejects_text_that_becomes_empty_after_cleaning() -> None:
    with pytest.raises(EmptyTextError, match="cleaning"):
        PreprocessingPipeline().process("https://example.org")


def test_pipeline_rejects_unsupported_language() -> None:
    with pytest.raises(UnsupportedLanguageError):
        PreprocessingPipeline().process("مرحبا بالعالم")


def test_pipeline_can_retain_unknown_language_when_policy_allows_it() -> None:
    pipeline = PreprocessingPipeline(PreprocessingConfig(reject_unsupported_languages=False))
    assert pipeline.process("مرحبا بالعالم").language == "unknown"


def test_environment_configuration_controls_all_primary_options() -> None:
    config = PreprocessingConfig.from_environment(
        {
            "OSINT_NLP_MIN_TEXT_LENGTH": "2",
            "OSINT_NLP_MAX_TEXT_LENGTH": "20",
            "OSINT_NLP_REMOVE_HTML": "false",
            "OSINT_NLP_REMOVE_URLS": "0",
            "OSINT_NLP_REMOVE_EMAILS": "no",
            "OSINT_NLP_LOWERCASE": "off",
            "OSINT_NLP_NORMALIZE_UNICODE": "false",
            "OSINT_NLP_NORMALIZE_MENTIONS": "false",
            "OSINT_NLP_NORMALIZE_USERNAMES": "false",
            "OSINT_NLP_REMOVE_PUNCTUATION": "false",
            "OSINT_NLP_REMOVE_NUMBERS": "true",
            "OSINT_NLP_REMOVE_STOPWORDS": "false",
            "OSINT_NLP_LEMMATIZE": "false",
            "OSINT_NLP_REJECT_UNSUPPORTED_LANGUAGES": "false",
            "OSINT_NLP_SUPPORTED_LANGUAGES": "en, es",
            "OSINT_NLP_PIPELINE_VERSION": "test-v1",
        }
    )

    assert config.min_text_length == 2
    assert config.max_text_length == 20
    assert not config.remove_html and not config.remove_urls and not config.remove_emails
    assert not config.lowercase and not config.normalize_unicode
    assert not config.normalize_mentions and not config.normalize_usernames
    assert not config.remove_punctuation and config.remove_numbers
    assert not config.remove_stopwords and not config.lemmatize
    assert not config.reject_unsupported_languages
    assert config.supported_languages == ("en", "es")
    assert config.pipeline_version == "test-v1"


@pytest.mark.parametrize(
    "values",
    [
        {"OSINT_NLP_MIN_TEXT_LENGTH": "zero"},
        {"OSINT_NLP_REMOVE_HTML": "perhaps"},
        {"OSINT_NLP_SUPPORTED_LANGUAGES": " , "},
    ],
)
def test_environment_configuration_rejects_invalid_values(values: dict[str, str]) -> None:
    with pytest.raises(InvalidConfigurationError):
        PreprocessingConfig.from_environment(values)


def test_configuration_rejects_invalid_cross_field_invariants() -> None:
    with pytest.raises(InvalidConfigurationError, match="cannot exceed"):
        PreprocessingConfig(min_text_length=3, max_text_length=2)
    with pytest.raises(InvalidConfigurationError, match="supported_languages"):
        PreprocessingConfig(supported_languages=())
    with pytest.raises(InvalidConfigurationError, match="pipeline_version"):
        PreprocessingConfig(pipeline_version=" ")


def test_stages_support_disabled_cleaning_and_normalization_options() -> None:
    cleaner = TextCleaner()
    assert cleaner.clean(
        "<b>x</b> https://x.io a@b.io", remove_html=False, remove_urls=False, remove_emails=False
    )
    normalizer = TextNormalizer()
    assert (
        normalizer.normalize(
            "Hi @A /u/B! 99",
            lowercase=False,
            normalize_unicode=False,
            normalize_mentions=False,
            normalize_usernames=False,
            remove_punctuation=False,
            remove_numbers=False,
        )
        == "Hi @A /u/B! 99"
    )


def test_token_stopword_and_lemmatization_stages() -> None:
    tokens = RegexTokenizer().tokenize("The running stories and dogs")
    filtered = StopwordFilter().remove(tokens, "en", enabled=True)
    assert filtered == ("running", "stories", "dogs")
    assert RuleBasedLemmatizer().lemmatize(filtered, "en", enabled=True) == ("run", "story", "dog")
    assert StopwordFilter().remove(tokens, "en", enabled=False) == tokens
    assert RuleBasedLemmatizer().lemmatize(tokens, "es", enabled=True) == tokens


def test_language_detector_fallback_and_script_policy() -> None:
    detector = HeuristicLanguageDetector()
    assert detector.detect("unusual terminology", DEFAULT_SUPPORTED_LANGUAGES) == "en"
    assert detector.detect("你好", DEFAULT_SUPPORTED_LANGUAGES) == "unknown"
    assert detector.detect("bonjour", ("es",)) == "unknown"


def test_configuration_helpers_support_defaults_and_failures() -> None:
    assert read_bool({}, "X", True)
    assert read_positive_int({}, "X", 2) == 2
    assert read_csv({}, "X", ("en",)) == ("en",)
    with pytest.raises(InvalidConfigurationError):
        read_positive_int({"X": "0"}, "X", 1)


def test_pipeline_emits_stage_logs(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("test.nlp")
    with caplog.at_level(logging.INFO, logger=logger.name):
        PreprocessingPipeline(logger=logger).process("A useful message")
    assert any(record.message == "nlp_stage_completed" for record in caplog.records)
    assert any(record.message == "nlp_pipeline_completed" for record in caplog.records)
