"""Parser converting raw Telethon messages into the unified message schema."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, cast

from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TELETHON_MESSAGE_MEDIA_DOCUMENT,
    TELETHON_MESSAGE_MEDIA_PHOTO,
    TelethonDocumentMedia,
    TelethonMessage,
    TelethonPhotoMedia,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.models import (
    ChannelRef,
    MediaInfo,
    MessageContent,
    MessageMetadata,
    ProcessingInfo,
    SenderRef,
    UnifiedMessage,
    _datetime_to_iso,
)

logger = logging.getLogger(__name__)

HASHTAG_PATTERN = re.compile(r"#(\w+)")
MENTION_PATTERN = re.compile(r"@(\w+)")
URL_PATTERN = re.compile(r"https?://[^\s]+")
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f000-\U0001f02f"  # Mahjong tiles
    "\U0001f0a0-\U0001f0ff"  # Playing cards
    "\U0001f300-\U0001f5ff"  # Misc symbols and pictographs
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f680-\U0001f6ff"  # Transport and map symbols
    "\U0001f900-\U0001f9ff"  # Supplemental symbols and pictographs
    "\U0001fa70-\U0001faff"  # Symbols and pictographs extended-A
    "\U0001f1e6-\U0001f1ff"  # Regional indicators (flags)
    "\U00002600-\U000027bf"  # Misc symbols and dingbats
    "\U00002b00-\U00002bff"  # Arrows
    "\U0000fe0e-\U0000fe0f"  # Variation selectors
    "\U000023e9-\U000023f3"  # Media control symbols
    "\U000023f8-\U000023fa"
    "\U00002b50"
    "\U00002764"
    "\U000027a1"
    "\U00003030"
    "\u00a9\u00ae"
    "]"
)
_ZWJ_VARIATION_CHARACTERS = frozenset({"\u200d", "\ufe0f"})

_VIDEO_EXTENSIONS = frozenset({"video/"})
_AUDIO_EXTENSIONS = frozenset({"audio/"})
_IMAGE_EXTENSIONS = frozenset({"image/"})


def extract_hashtags(text: str | None) -> list[str]:
    """Extract hashtag names (without the ``#`` prefix) from text."""
    if not text:
        return []
    return HASHTAG_PATTERN.findall(text)


def extract_mentions(text: str | None) -> list[str]:
    """Extract mention names (without the ``@`` prefix) from text."""
    if not text:
        return []
    return MENTION_PATTERN.findall(text)


def extract_urls(text: str | None) -> list[str]:
    """Extract http(s) URLs from text."""
    if not text:
        return []
    return URL_PATTERN.findall(text)


def extract_emojis(text: str | None) -> list[str]:
    """Extract individual emoji characters from text.

    Variation selectors and the zero-width joiner are stripped from the result
    so consecutive characters do not pollute the emoji list. Occurrences are
    kept (mirroring hashtag extraction); deduplication is left to the consumer.
    """
    if not text:
        return []
    return [char for char in EMOJI_PATTERN.findall(text) if char not in _ZWJ_VARIATION_CHARACTERS]


def normalize_timestamp(value: datetime | None) -> str | None:
    """Normalize a datetime to a UTC ISO-8601 string (``None`` in, ``None`` out)."""
    return _datetime_to_iso(value)


def _photo_dimensions(sizes: Any | None) -> tuple[int | None, int | None]:
    """Return the widest photo dimensions among the given Telegram sizes."""
    best_width: int | None = None
    best_height: int | None = None
    best_area = -1
    for size in sizes or []:
        width = getattr(size, "w", None)
        height = getattr(size, "h", None)
        if width is None or height is None:
            continue
        area = int(width) * int(height)
        if area > best_area:
            best_area = area
            best_width = int(width)
            best_height = int(height)
    return best_width, best_height


def _document_attributes(
    attributes: Any | None, mime_type: str
) -> tuple[str, str | None, int | None, int | None, float | None]:
    """Derive type, filename and dimensions from a document's attributes.

    Returns:
        A tuple of ``(media_type, filename, width, height, duration)``.
    """
    media_type = "document"
    filename: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None

    if mime_type.startswith(tuple(_VIDEO_EXTENSIONS)):
        media_type = "video"
    elif mime_type.startswith(tuple(_AUDIO_EXTENSIONS)):
        media_type = "audio"
    elif mime_type.startswith(tuple(_IMAGE_EXTENSIONS)):
        media_type = "image"

    for attribute in attributes or []:
        name = type(attribute).__name__
        if name == "DocumentAttributeFilename":
            filename = getattr(attribute, "file_name", None)
        elif name == "DocumentAttributeVideo":
            media_type = "video"
            width = getattr(attribute, "w", None)
            height = getattr(attribute, "h", None)
            duration = getattr(attribute, "duration", None)
        elif name == "DocumentAttributeAudio":
            media_type = "audio"
            duration = getattr(attribute, "duration", None)
        elif name == "DocumentAttributeAnimated":
            media_type = "animation"
        elif name == "DocumentAttributeSticker":
            media_type = "sticker"
    return media_type, filename, width, height, duration


def _extract_media(message: TelethonMessage) -> MediaInfo:
    """Extract media metadata (never bytes) from a Telethon message."""
    media = getattr(message, "media", None)
    if media is None:
        return MediaInfo()

    if isinstance(media, TELETHON_MESSAGE_MEDIA_PHOTO):
        photo = cast(TelethonPhotoMedia, media).photo
        width, height = _photo_dimensions(getattr(photo, "sizes", None))
        file_id = getattr(photo, "id", None)
        return MediaInfo(
            has_media=True,
            type="photo",
            telegram_file_id=str(file_id) if file_id is not None else None,
            width=width,
            height=height,
        )

    if isinstance(media, TELETHON_MESSAGE_MEDIA_DOCUMENT):
        document = cast(TelethonDocumentMedia, media).document
        mime_type = getattr(document, "mime_type", None) or ""
        media_type, filename, width, height, duration = _document_attributes(
            getattr(document, "attributes", None), mime_type
        )
        thumb_width, thumb_height = _photo_dimensions(
            getattr(getattr(document, "thumb", None), "sizes", None)
        )
        file_id = getattr(document, "id", None)
        return MediaInfo(
            has_media=True,
            type=media_type,
            telegram_file_id=str(file_id) if file_id is not None else None,
            filename=filename,
            mime_type=mime_type or None,
            width=width or thumb_width,
            height=height or thumb_height,
            duration=duration,
            size_bytes=getattr(document, "size", None),
        )

    logger.debug("media_type_unhandled", extra={"media_type": type(media).__name__})
    return MediaInfo()


def _extract_channel(message: TelethonMessage) -> ChannelRef:
    """Extract the publishing channel identity from a Telethon message."""
    chat = getattr(message, "chat", None)
    channel_id = getattr(chat, "id", None) if chat is not None else None
    if channel_id is None:
        chat_id = getattr(message, "chat_id", None)
        if chat_id is not None:
            channel_id = abs(int(chat_id))

    username = getattr(chat, "username", None) if chat is not None else None

    title = getattr(chat, "title", None) if chat is not None else None
    if not title and chat is not None:
        first_name = getattr(chat, "first_name", "") or ""
        last_name = getattr(chat, "last_name", "") or ""
        title = f"{first_name} {last_name}".strip() or None

    return ChannelRef(
        id=str(channel_id) if channel_id is not None else None,
        username=username,
        title=title,
    )


def _extract_sender(message: TelethonMessage) -> SenderRef:
    """Extract the author identity from a Telethon message."""
    sender = getattr(message, "sender", None)
    sender_id = getattr(message, "sender_id", None)
    if sender_id is None and sender is not None:
        sender_id = getattr(sender, "id", None)

    username = getattr(sender, "username", None) if sender is not None else None

    display_name: str | None = None
    if sender is not None:
        first_name = getattr(sender, "first_name", "") or ""
        last_name = getattr(sender, "last_name", "") or ""
        display_name = f"{first_name} {last_name}".strip() or getattr(sender, "title", None)

    return SenderRef(
        id=str(sender_id) if sender_id is not None else None,
        username=username,
        display_name=display_name,
    )


def _extract_reply_count(message: TelethonMessage) -> int:
    """Return the number of replies for a message (0 when unavailable)."""
    replies = getattr(message, "replies", None)
    if replies is None:
        return 0
    count = getattr(replies, "replies", None)
    return int(count) if count is not None else 0


class TelegramParser:
    """Parse raw Telethon messages into the unified message schema."""

    PLATFORM = "telegram"

    def parse(self, message: TelethonMessage) -> UnifiedMessage:
        """Parse a single Telethon message into a :class:`UnifiedMessage`.

        Args:
            message: Raw Telethon message to convert.

        Returns:
            A :class:`UnifiedMessage` following the unified schema.
        """
        text = message.text or ""
        content = MessageContent(
            id=str(message.id) if message.id is not None else None,
            text=text,
            hashtags=extract_hashtags(text),
            mentions=extract_mentions(text),
            urls=extract_urls(text),
            emojis=extract_emojis(text),
        )
        views = getattr(message, "views", None)
        forwards = getattr(message, "forwards", None)
        metadata = MessageMetadata(
            timestamp=normalize_timestamp(message.date),
            views=int(views) if views is not None else 0,
            forwards=int(forwards) if forwards is not None else 0,
            reply_count=_extract_reply_count(message),
            edit_date=normalize_timestamp(getattr(message, "edit_date", None)),
        )
        return UnifiedMessage(
            platform=self.PLATFORM,
            channel=_extract_channel(message),
            sender=_extract_sender(message),
            message=content,
            media=_extract_media(message),
            metadata=metadata,
            processing=ProcessingInfo(),
        )

    def parse_batch(self, messages: list[TelethonMessage]) -> list[UnifiedMessage]:
        """Parse multiple Telethon messages into unified messages.

        Args:
            messages: Raw Telethon messages to convert.

        Returns:
            List of parsed :class:`UnifiedMessage` objects, one per input.
        """
        return [self.parse(message) for message in messages]
