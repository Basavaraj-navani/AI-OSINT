"""Telegram OSINT Collector package."""

from drug_trafficking_osint.infrastructure.collectors.telegram.client import TelegramClient
from drug_trafficking_osint.infrastructure.collectors.telegram.collector import TelegramCollector
from drug_trafficking_osint.infrastructure.collectors.telegram.filters import MessageFilter
from drug_trafficking_osint.infrastructure.collectors.telegram.media_downloader import (
    TelegramMediaDownloader,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.models import (
    ChannelRef,
    MediaInfo,
    MessageContent,
    MessageMetadata,
    ProcessingInfo,
    SenderRef,
    UnifiedMessage,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.parser import TelegramParser

__all__ = [
    "ChannelRef",
    "MediaInfo",
    "MessageContent",
    "MessageFilter",
    "MessageMetadata",
    "ProcessingInfo",
    "SenderRef",
    "TelegramClient",
    "TelegramCollector",
    "TelegramMediaDownloader",
    "TelegramParser",
    "UnifiedMessage",
]
