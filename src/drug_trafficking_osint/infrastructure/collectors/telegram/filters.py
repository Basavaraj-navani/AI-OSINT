"""Message filtering for Telegram collector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from drug_trafficking_osint.infrastructure.collectors.telegram._types import TelethonMessage


@dataclass
class MessageFilter:
    """Configuration for message filtering."""

    min_length: int = 1
    max_length: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    keywords: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    exclude_service_messages: bool = True
    exclude_empty: bool = True
    exclude_deleted: bool = True
    public_only: bool = True
    user_id: int | None = None


def apply_filters(message: TelethonMessage, filter_config: MessageFilter) -> bool:
    """Apply all filters to a message. Returns True if message passes all filters."""
    if filter_config.exclude_deleted and getattr(message, "deleted", False):
        return False

    if filter_config.exclude_service_messages and getattr(message, "action", None):
        return False

    if filter_config.exclude_empty and not getattr(message, "text", None):
        return False

    if filter_config.user_id and message.from_id:
        sender_id = getattr(message.from_id, "user_id", None)
        if sender_id != filter_config.user_id:
            return False

    if message.text:
        text_len = len(message.text)
        if text_len < filter_config.min_length:
            return False
        if filter_config.max_length and text_len > filter_config.max_length:
            return False

    if filter_config.start_date and message.date < filter_config.start_date:
        return False

    if filter_config.end_date and message.date > filter_config.end_date:
        return False

    if filter_config.keywords and message.text:
        text_lower = message.text.lower()
        if not any(kw.lower() in text_lower for kw in filter_config.keywords):
            return False

    return True


def filter_messages(
    messages: list[TelethonMessage],
    filter_config: MessageFilter,
) -> list[TelethonMessage]:
    """Filter a list of messages."""
    return [msg for msg in messages if apply_filters(msg, filter_config)]
