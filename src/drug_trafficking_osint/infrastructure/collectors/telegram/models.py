"""Unified, platform-agnostic message schema used by the whole data pipeline.

A single :class:`UnifiedMessage` represents exactly one collected message
(Telegram today, Instagram in the future). Emojis, hashtags, media, URLs and
mentions are properties of the message and are stored inside the same document
-- never in separate collections.

Only ``platform`` differs between sources; downstream consumers (NLP, storage,
exporter) must never need to know where a message came from.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _datetime_to_iso(value: datetime | None) -> str | None:
    """Convert a datetime to an ISO-8601 string, normalizing to UTC.

    MongoDB stores timestamps as ISO strings so that exports are JSON
    compatible and lexicographic ordering matches chronological ordering.

    Args:
        value: Naive or aware datetime, or ``None``.

    Returns:
        ISO-8601 UTC string or ``None`` when the input is ``None``.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ChannelRef:
    """Identity of the channel or account that published the message."""

    id: str | None = None
    username: str | None = None
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``channel`` sub-document."""
        return {"id": self.id, "username": self.username, "title": self.title}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ChannelRef:
        """Build a channel reference from a ``channel`` sub-document."""
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            title=data.get("title"),
        )


@dataclass(frozen=True, slots=True)
class SenderRef:
    """Identity of the user (or anonymous author) behind a message."""

    id: str | None = None
    username: str | None = None
    display_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``sender`` sub-document."""
        return {"id": self.id, "username": self.username, "display_name": self.display_name}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SenderRef:
        """Build a sender reference from a ``sender`` sub-document."""
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            display_name=data.get("display_name"),
        )


@dataclass(frozen=True, slots=True)
class MessageContent:
    """Textual content and inline annotations of a message."""

    id: str | None = None
    text: str = ""
    clean_text: str | None = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    emojis: list[str] = field(default_factory=list)
    language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``message`` sub-document."""
        return {
            "id": self.id,
            "text": self.text,
            "clean_text": self.clean_text,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "urls": self.urls,
            "emojis": self.emojis,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MessageContent:
        """Build message content from a ``message`` sub-document."""
        return cls(
            id=data.get("id"),
            text=data.get("text", ""),
            clean_text=data.get("clean_text"),
            hashtags=list(data.get("hashtags") or []),
            mentions=list(data.get("mentions") or []),
            urls=list(data.get("urls") or []),
            emojis=list(data.get("emojis") or []),
            language=data.get("language"),
        )


@dataclass(frozen=True, slots=True)
class MediaInfo:
    """Metadata of attached media.

    Media bytes are never stored inside MongoDB; only ``local_path`` (and a
    content ``hash``) are persisted after downloading to ``datasets/media/``.
    """

    has_media: bool = False
    type: str | None = None
    telegram_file_id: str | None = None
    filename: str | None = None
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    size_bytes: int | None = None
    local_path: str | None = None
    hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``media`` sub-document."""
        return {
            "has_media": self.has_media,
            "type": self.type,
            "telegram_file_id": self.telegram_file_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "size_bytes": self.size_bytes,
            "local_path": self.local_path,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MediaInfo:
        """Build media info from a ``media`` sub-document."""
        return cls(
            has_media=bool(data.get("has_media")),
            type=data.get("type"),
            telegram_file_id=data.get("telegram_file_id"),
            filename=data.get("filename"),
            mime_type=data.get("mime_type"),
            width=data.get("width"),
            height=data.get("height"),
            duration=data.get("duration"),
            size_bytes=data.get("size_bytes"),
            local_path=data.get("local_path"),
            hash=data.get("hash"),
        )


@dataclass(frozen=True, slots=True)
class MessageMetadata:
    """Engagement and timestamp data attached to a message."""

    timestamp: str | None = None
    views: int = 0
    forwards: int = 0
    reply_count: int = 0
    edit_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``metadata`` sub-document."""
        return {
            "timestamp": self.timestamp,
            "views": self.views,
            "forwards": self.forwards,
            "reply_count": self.reply_count,
            "edit_date": self.edit_date,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MessageMetadata:
        """Build message metadata from a ``metadata`` sub-document."""
        return cls(
            timestamp=data.get("timestamp"),
            views=int(data.get("views") or 0),
            forwards=int(data.get("forwards") or 0),
            reply_count=int(data.get("reply_count") or 0),
            edit_date=data.get("edit_date"),
        )


@dataclass(frozen=True, slots=True)
class ProcessingInfo:
    """NLP/NER/graph analysis state attached to a stored message."""

    nlp_completed: bool = False
    ner_completed: bool = False
    graph_completed: bool = False
    risk_score: float | None = None
    classification: str | None = None
    entities: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``processing`` sub-document."""
        return {
            "nlp_completed": self.nlp_completed,
            "ner_completed": self.ner_completed,
            "graph_completed": self.graph_completed,
            "risk_score": self.risk_score,
            "classification": self.classification,
            "entities": self.entities,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessingInfo:
        """Build processing state from a ``processing`` sub-document."""
        return cls(
            nlp_completed=bool(data.get("nlp_completed")),
            ner_completed=bool(data.get("ner_completed")),
            graph_completed=bool(data.get("graph_completed")),
            risk_score=data.get("risk_score"),
            classification=data.get("classification"),
            entities=list(data.get("entities") or []),
        )


@dataclass(frozen=True, slots=True)
class UnifiedMessage:
    """Single platform-independent message.

    Attributes:
        platform: Source platform identifier (e.g. ``"telegram"``).
        channel: Publishing channel or account.
        sender: Authoring user (anonymous authors yield ``None`` values).
        message: Text content with hashtags, mentions, URLs and emojis.
        media: Media metadata; bytes are never embedded.
        metadata: Timestamp and engagement counters.
        processing: NLP/NER/graph analysis state.
    """

    platform: str
    channel: ChannelRef = field(default_factory=ChannelRef)
    sender: SenderRef = field(default_factory=SenderRef)
    message: MessageContent = field(default_factory=MessageContent)
    media: MediaInfo = field(default_factory=MediaInfo)
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    processing: ProcessingInfo = field(default_factory=ProcessingInfo)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the MongoDB ``telegram_messages`` document.

        The returned dictionary exactly matches the unified schema, always
        including every key (with ``None`` defaults) so documents stay
        structurally consistent regardless of the source platform.
        """
        return {
            "platform": self.platform,
            "channel": self.channel.to_dict(),
            "sender": self.sender.to_dict(),
            "message": self.message.to_dict(),
            "media": self.media.to_dict(),
            "metadata": self.metadata.to_dict(),
            "processing": self.processing.to_dict(),
        }

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> UnifiedMessage:
        """Hydrate a unified message from a stored MongoDB document.

        Unknown keys (e.g. ``_id``) are ignored, so repository results can be
        fed straight back into the model.
        """
        return cls(
            platform=str(document.get("platform") or "unknown"),
            channel=ChannelRef.from_dict(document.get("channel") or {}),
            sender=SenderRef.from_dict(document.get("sender") or {}),
            message=MessageContent.from_dict(document.get("message") or {}),
            media=MediaInfo.from_dict(document.get("media") or {}),
            metadata=MessageMetadata.from_dict(document.get("metadata") or {}),
            processing=ProcessingInfo.from_dict(document.get("processing") or {}),
        )
