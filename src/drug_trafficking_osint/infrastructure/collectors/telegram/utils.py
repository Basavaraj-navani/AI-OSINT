"""Utility functions for Telegram collector."""

from __future__ import annotations

import re
from datetime import datetime
from typing import cast

from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TELETHON_MESSAGE_MEDIA_DOCUMENT,
    TELETHON_MESSAGE_MEDIA_PHOTO,
    TELETHON_MESSAGE_MEDIA_WEB_PAGE,
    TelethonDocumentMedia,
    TelethonMessage,
)

HASHTAG_PATTERN = re.compile(r"#(\w+)")
MENTION_PATTERN = re.compile(r"@(\w+)")
URL_PATTERN = re.compile(r"https?://[^\s]+")


def extract_hashtags(text: str) -> list[str]:
    """Extract hashtags from text."""
    return HASHTAG_PATTERN.findall(text)


def extract_mentions(text: str) -> list[str]:
    """Extract mentions from text."""
    return MENTION_PATTERN.findall(text)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    return URL_PATTERN.findall(text)


def detect_media_type(message: TelethonMessage) -> str | None:
    """Detect media type from message."""
    if not message.media:
        return None

    media = message.media
    if isinstance(media, TELETHON_MESSAGE_MEDIA_PHOTO):
        return "photo"
    if isinstance(media, TELETHON_MESSAGE_MEDIA_DOCUMENT):
        document = cast(TelethonDocumentMedia, media).document
        mime_type = getattr(document, "mime_type", None)
        if mime_type and mime_type.startswith("video"):
            return "video"
        if mime_type and mime_type.startswith("audio"):
            return "audio"
        return "document"
    if isinstance(media, TELETHON_MESSAGE_MEDIA_WEB_PAGE):
        return "webpage"

    return "unknown"


def normalize_timestamp(dt: datetime) -> str:
    """Normalize timestamp to ISO 8601 format."""
    return dt.isoformat()


def sanitize_text(text: str) -> str:
    """Sanitize text by removing extra whitespace."""
    return " ".join(text.split())


def remove_duplicate_messages(
    messages: list[TelethonMessage],
    key: str = "id",
) -> list[TelethonMessage]:
    """Remove duplicate messages based on a key."""
    seen: set[object] = set()
    unique: list[TelethonMessage] = []
    for msg in messages:
        msg_id: object = getattr(msg, key, None)
        if msg_id not in seen:
            seen.add(msg_id)
            unique.append(msg)
    return unique
