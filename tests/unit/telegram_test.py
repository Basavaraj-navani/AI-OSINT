"""Test multiple Telegram channels using the collector infrastructure."""

import asyncio

import pytest

from drug_trafficking_osint.core.config import Settings
from drug_trafficking_osint.infrastructure.collectors.database.repository import MongoRepository
from drug_trafficking_osint.infrastructure.collectors.telegram import (
    MessageFilter,
    TelegramClient,
    TelegramCollector,
    UnifiedMessage,
)
from drug_trafficking_osint.infrastructure.database.mongodb import MongoDB

TARGET_CHANNELS = [
    "telegram",
    "durov",
]

MESSAGES_PER_CHANNEL = 5

pytestmark = pytest.mark.integration


async def test_multiple_channels() -> dict[str, list[UnifiedMessage]]:
    """Test collecting messages from multiple channels."""
    settings = Settings.from_environment()

    # Ensure interactive authentication is handled first
    from pathlib import Path

    from telethon import TelegramClient as RawTelethonClient

    session_path = Path.cwd() / "sessions" / settings.telegram.session_name
    session_path.parent.mkdir(parents=True, exist_ok=True)
    raw_client = RawTelethonClient(
        str(session_path), settings.telegram.api_id, settings.telegram.api_hash
    )
    print("Checking authentication (will prompt for phone if not authorized)...")
    await raw_client.start()
    await raw_client.disconnect()

    client = TelegramClient(settings)

    mongodb = MongoDB(settings)
    mongodb.connect()
    sink = MongoRepository(mongodb.get_database())
    sink.create_indexes()

    async with client:
        collector = TelegramCollector(client, sink=sink)

        results = {}

        for channel in TARGET_CHANNELS:
            print(f"\n{'=' * 60}")
            print(f"Fetching from @{channel}...")
            print(f"{'=' * 60}")

            messages = []

            # Test filter: only grab messages with at least 20 characters
            test_filter = MessageFilter(min_length=20, exclude_empty=True)

            async for msg in collector.collect_channel(
                channel, limit=MESSAGES_PER_CHANNEL, filter_config=test_filter
            ):
                messages.append(msg)
                print(f"\n--- Message ID: {msg.message.id} ---")
                print(f"Platform:   {msg.platform}")
                print(f"Channel:    {msg.channel.username or msg.channel.id}")
                print(f"Channel title: {msg.channel.title}")
                print(f"Date:       {msg.metadata.timestamp}")
                print(f"Sender:     {msg.sender.username or msg.sender.id}")
                print(f"Views:      {msg.metadata.views}")
                print(f"Forwards:   {msg.metadata.forwards}")
                print(f"Replies:    {msg.metadata.reply_count}")
                print(f"Media:      {msg.media.to_dict()}")
                print(f"Hashtags:   {msg.message.hashtags}")
                print(f"Mentions:   {msg.message.mentions}")
                print(f"URLs:       {msg.message.urls}")
                print(f"Emojis:     {msg.message.emojis}")
                print(f"Text:       {msg.message.text[:120] if msg.message.text else 'N/A'}...")

            results[channel] = messages
            print(f"\nCollected {len(messages)} messages from @{channel}")

    return results


async def main():
    print("Testing multi-channel collection...")
    print(f"Target channels: {TARGET_CHANNELS}")
    print(f"Messages per channel: {MESSAGES_PER_CHANNEL}")

    try:
        results = await test_multiple_channels()

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        total = 0
        for channel, msgs in results.items():
            print(f"@{channel}: {len(msgs)} messages")
            total += len(msgs)
        print(f"Total: {total} messages")
        print("Test completed successfully!")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
