"""Stable defaults and compiled patterns used by the NLP preprocessing adapters."""

from __future__ import annotations

import re

DEFAULT_MAX_TEXT_LENGTH = 10_000
DEFAULT_MIN_TEXT_LENGTH = 1
DEFAULT_PIPELINE_VERSION = "1.0.0"
DEFAULT_SUPPORTED_LANGUAGES = ("en", "es", "fr", "de", "pt")

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.IGNORECASE)
MENTION_PATTERN = re.compile(r"(?<!\w)@[A-Za-z0-9_]{1,64}\b")
USERNAME_PATTERN = re.compile(r"(?<!\w)(?:/u/|u/)[A-Za-z0-9_-]{1,64}\b", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)
PUNCTUATION_PATTERN = re.compile(r"[^\w\s'-]", re.UNICODE)
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f-\x9f]")

LANGUAGE_STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset({"the", "and", "for", "with", "this", "that", "from", "are", "was", "you"}),
    "es": frozenset({"el", "la", "los", "las", "de", "que", "y", "en", "para", "con"}),
    "fr": frozenset({"le", "la", "les", "de", "des", "et", "en", "pour", "avec", "une"}),
    "de": frozenset({"der", "die", "das", "und", "mit", "für", "von", "ist", "den", "ein"}),
    "pt": frozenset({"o", "a", "os", "as", "de", "e", "em", "para", "com", "uma"}),
}
