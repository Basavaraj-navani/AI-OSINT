"""Orchestrates Telegram data collection into unified messages."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Protocol

from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TelethonClient,
    TelethonMessage,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.client import TelegramClient
from drug_trafficking_osint.infrastructure.collectors.telegram.filters import (
    MessageFilter,
    apply_filters,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.media_downloader import (
    TelegramMediaDownloader,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.models import (
    ChannelRef,
    UnifiedMessage,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.parser import TelegramParser


class MessageSink(Protocol):
    """Persists unified messages without leaking MongoDB internals to collectors.

    The collector only depends on this abstraction; concrete sinks (e.g. the
    Mongo repository) are injected through the constructor.
    """

    def save_message(self, message: UnifiedMessage) -> object:
        """Persist a single unified message.

        Args:
            message: The parsed message to persist.

        Returns:
            A platform-specific persistence identifier (e.g. an ObjectId).
        """
        ...

    def save_channel(self, channel: ChannelRef) -> object:
        """Persist (or upsert) a channel that messages were collected from.

        Args:
            channel: The publishing channel identity.
        """
        ...


def _channel_ref_from_entity(entity: object) -> ChannelRef:
    """Build a channel reference from a resolved Telethon entity."""
    entity_id = getattr(entity, "id", None)
    username = getattr(entity, "username", None)
    title = getattr(entity, "title", None)
    if not title:
        first_name = getattr(entity, "first_name", "") or ""
        last_name = getattr(entity, "last_name", "") or ""
        title = f"{first_name} {last_name}".strip() or None
    return ChannelRef(
        id=str(abs(int(entity_id))) if entity_id is not None else None,
        username=username,
        title=title,
    )


class TelegramCollector:
    """Coordinates message collection from Telegram channels.

    Flow: ``Telethon message -> TelegramParser -> UnifiedMessage ->
    optional media download -> optional MessageSink.save_message()``.
    """

    def __init__(
        self,
        client: TelegramClient,
        *,
        sink: MessageSink | None = None,
        media_dir: str | Path | None = None,
    ) -> None:
        """Initialize the collector.

        Args:
            client: Wrapper owning the connected Telethon client.
            sink: Optional persistence target implementing :class:`MessageSink`.
            media_dir: Optional directory for media downloads. When omitted,
                media bytes are not downloaded.
        """
        self._client = client
        self._parser = TelegramParser()
        self._sink = sink
        self._media_downloader = (
            TelegramMediaDownloader(media_dir) if media_dir is not None else None
        )

    async def collect_channel(
        self,
        channel: str,
        limit: int = 100,
        filter_config: MessageFilter | None = None,
    ) -> AsyncIterator[UnifiedMessage]:
        """Collect messages from a single channel.

        Args:
            channel: Channel username, id, or invitation link.
            limit: Maximum number of messages to iterate.
            filter_config: Optional filters applied before parsing.

        Yields:
            Parsed :class:`UnifiedMessage` objects.

        Raises:
            RuntimeError: If the underlying client is not connected.
        """
        telethon_client = self._client.get_client()
        if not telethon_client:
            raise RuntimeError("Client not connected. Call connect() first.")

        entity = await telethon_client.get_entity(channel)

        if self._sink is not None:
            self._sink.save_channel(_channel_ref_from_entity(entity))

        async for message in telethon_client.iter_messages(entity, limit=limit):
            if filter_config and not apply_filters(message, filter_config):
                continue

            parsed = self._parser.parse(message)
            parsed = await self._attach_media(telethon_client, message, parsed)

            if self._sink is not None:
                self._sink.save_message(parsed)

            yield parsed

    async def collect_channels(
        self,
        channels: list[str],
        limit: int = 100,
        filter_config: MessageFilter | None = None,
    ) -> AsyncIterator[UnifiedMessage]:
        """Collect messages from multiple channels, one after the other."""
        for channel in channels:
            async for msg in self.collect_channel(channel, limit, filter_config):
                yield msg

    async def collect_recent_messages(
        self,
        channel: str,
        limit: int = 100,
        filter_config: MessageFilter | None = None,
    ) -> list[UnifiedMessage]:
        """Collect recent messages from a channel into a list."""
        messages: list[UnifiedMessage] = []
        async for msg in self.collect_channel(channel, limit, filter_config):
            messages.append(msg)
        return messages

    async def collect_between_dates(
        self,
        channel: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        filter_config: MessageFilter | None = None,
    ) -> list[UnifiedMessage]:
        """Collect messages within a date range."""
        if filter_config is None:
            filter_config = MessageFilter()
        filter_config.start_date = start_date
        filter_config.end_date = end_date

        return await self.collect_recent_messages(channel, limit, filter_config)

    async def collect_user_messages(
        self,
        channel: str,
        user_id: int,
        limit: int = 100,
        filter_config: MessageFilter | None = None,
    ) -> list[UnifiedMessage]:
        """Collect messages from a specific user in a channel."""
        if filter_config is None:
            filter_config = MessageFilter()
        filter_config.user_id = user_id

        return await self.collect_recent_messages(channel, limit, filter_config)

    async def _attach_media(
        self,
        telethon_client: TelethonClient,
        message: TelethonMessage,
        parsed: UnifiedMessage,
    ) -> UnifiedMessage:
        """Download media (when enabled) and record its local path and hash."""
        if self._media_downloader is None or not parsed.media.has_media:
            return parsed

        downloaded = await self._media_downloader.download(telethon_client, message, parsed.media)
        if downloaded is None:
            return parsed

        return replace(
            parsed,
            media=replace(
                parsed.media,
                local_path=downloaded.local_path,
                hash=downloaded.sha256,
            ),
        )
