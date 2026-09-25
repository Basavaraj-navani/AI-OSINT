"""Text-cleaning stage that removes machine-unhelpful OSINT artifacts."""

from __future__ import annotations

from drug_trafficking_osint.infrastructure.nlp.constants import (
    CONTROL_CHARACTER_PATTERN,
    EMAIL_PATTERN,
    HTML_TAG_PATTERN,
    URL_PATTERN,
    WHITESPACE_PATTERN,
)


class TextCleaner:
    """Remove HTML, URLs, emails, control characters, and excess whitespace."""

    def clean(self, text: str, *, remove_html: bool, remove_urls: bool, remove_emails: bool) -> str:
        """Return cleaned text without changing its lexical case or Unicode form.

        Args:
            text: Validated raw text.
            remove_html: Whether markup tags are removed.
            remove_urls: Whether web addresses are removed.
            remove_emails: Whether email addresses are removed.
        """
        cleaned = CONTROL_CHARACTER_PATTERN.sub(" ", text)
        if remove_html:
            cleaned = HTML_TAG_PATTERN.sub(" ", cleaned)
        if remove_urls:
            cleaned = URL_PATTERN.sub(" ", cleaned)
        if remove_emails:
            cleaned = EMAIL_PATTERN.sub(" ", cleaned)
        return WHITESPACE_PATTERN.sub(" ", cleaned).strip()
