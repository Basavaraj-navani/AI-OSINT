"""Test MongoDB connection and MongoRepository implementation."""

import asyncio
import datetime
import sys

from drug_trafficking_osint.core.config import Settings
from drug_trafficking_osint.infrastructure.collectors.database.repository import MongoRepository
from drug_trafficking_osint.infrastructure.collectors.telegram import TelegramClient
from drug_trafficking_osint.infrastructure.collectors.telegram.collector import (
    _channel_ref_from_entity,
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
from drug_trafficking_osint.infrastructure.database.mongodb import MongoDB

# EDIT ME: List the Telegram channels to fetch metadata for and store in the DB.
TARGET_CHANNELS = [
    "telegram",
    "durov",
]


def build_fake_message() -> UnifiedMessage:
    """Generate a UnifiedMessage document with realistic fake data."""
    now = datetime.datetime.now(datetime.UTC).isoformat()
    return UnifiedMessage(
        platform="telegram",
        channel=ChannelRef(id="123456789", username="test_drug_channel", title="Test Drug Channel"),
        sender=SenderRef(id="98765", username="test_dealer", display_name="Test Dealer"),
        message=MessageContent(
            id="1001",
            text=(
                "Testing the repository flow with realistic fake data "
                "#test #osint @test_buyer https://example.com 🚀💊"
            ),
            hashtags=["test", "osint"],
            mentions=["test_buyer"],
            urls=["https://example.com"],
            emojis=["🚀", "💊"],
        ),
        media=MediaInfo(has_media=False),
        metadata=MessageMetadata(timestamp=now, views=100, forwards=5, reply_count=2),
        processing=ProcessingInfo(),
    )


async def fetch_and_store_channel_metadata(settings: Settings, repo: MongoRepository) -> None:
    """Resolve each target channel from Telegram and upsert its metadata.

    Stores ``{channel_id, username, title, platform}`` into ``telegram_channels``.
    """
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
    async with client:
        telethon_client = client.get_client()
        for channel in TARGET_CHANNELS:
            entity = await telethon_client.get_entity(channel)
            channel_ref = _channel_ref_from_entity(entity)
            repo.save_channel(channel_ref)
            print(
                f"[OK] Stored channel @{channel} -> "
                f"id={channel_ref.id}, username={channel_ref.username}, title={channel_ref.title}"
            )


def run_test():
    """Run the MongoDB connection and repository tests."""
    print("============================================================")
    print("Testing MongoDB and MongoRepository")
    print("============================================================")

    # Prepare settings and components
    settings = Settings.from_environment()
    mongodb = MongoDB(settings)
    repo = None
    inserted_id = None

    try:
        # STEP 1: Create the MongoDB connection and Verify ping
        mongodb.connect()
        db = mongodb.get_database()
        result = db.command("ping")
        assert result.get("ok") == 1.0, "Ping did not return ok=1.0"
        print("[OK] Connected to MongoDB")

        # STEP 2: Create a MongoRepository instance
        repo = MongoRepository(db)

        # STEP 3: Create the required indexes
        repo.create_indexes()
        print("[OK] Indexes created")

        # STEP 3b: Remove any leftovers from previous runs (idempotent reruns)
        repo.delete_message("1001")
        repo.db["telegram_channels"].delete_one({"channel_id": "123456789"})
        print("[OK] Cleared previous test documents")

        # STEP 4: Generate a fake UnifiedMessage document
        fake_message = build_fake_message()

        # STEP 5: Insert the fake document
        inserted_id = repo.save_message(fake_message)
        assert inserted_id is not None, "save_message returned None for inserted ObjectId"
        print(f"[OK] Insert Successful. ObjectId: {inserted_id}")

        # STEP 5b: Upsert the channel into telegram_channels
        repo.save_channel(fake_message.channel)
        channel_doc = repo.db["telegram_channels"].find_one({"channel_id": "123456789"})
        assert channel_doc is not None, "Channel was not stored in telegram_channels"
        assert channel_doc["title"] == "Test Drug Channel", "Channel title mismatch"
        channel_count = repo.count_channels()
        print(f"[OK] Channel upserted into telegram_channels. Channel count: {channel_count}")

        # STEP 5c: Fetch real metadata for each target channel and store it
        if TARGET_CHANNELS:
            asyncio.run(fetch_and_store_channel_metadata(settings, repo))
            print(f"[OK] Fetched metadata for {len(TARGET_CHANNELS)} channels")

        # STEP 6: Retrieve the document and verify nested schema fields
        retrieved_msg = repo.get_message(inserted_id)
        assert retrieved_msg is not None, "Failed to retrieve the inserted document"
        assert retrieved_msg["platform"] == "telegram", "Platform mismatch"
        assert retrieved_msg["channel"]["id"] == "123456789", "Channel id mismatch"
        assert (
            retrieved_msg["channel"]["username"] == "test_drug_channel"
        ), "Channel username mismatch"
        assert retrieved_msg["sender"]["id"] == "98765", "Sender id mismatch"
        assert (
            retrieved_msg["message"]["text"] == fake_message.message.text
        ), "Message text mismatch"
        assert retrieved_msg["message"]["hashtags"] == ["test", "osint"], "Hashtags mismatch"
        assert retrieved_msg["message"]["mentions"] == ["test_buyer"], "Mentions mismatch"
        assert retrieved_msg["message"]["emojis"] == ["🚀", "💊"], "Emojis mismatch"
        assert retrieved_msg["metadata"]["views"] == 100, "Views mismatch"
        print("[OK] Read Successful")

        # STEP 7: Update processing results and verify nested update
        processing_update = ProcessingInfo(
            nlp_completed=True,
            risk_score=0.85,
            classification="high_risk",
            entities=[{"type": "PERSON", "text": "Test Dealer"}],
        )
        update_result = repo.update_processing_results(inserted_id, processing_update)
        assert update_result is True, "update_processing_results did not return True"

        updated_msg = repo.get_message(inserted_id)
        assert updated_msg["processing"]["nlp_completed"] is True, "nlp_completed not updated"
        assert updated_msg["processing"]["risk_score"] == 0.85, "risk_score not updated"
        assert (
            updated_msg["processing"]["classification"] == "high_risk"
        ), "classification not updated"
        print("[OK] Processing Update Successful")

        # STEP 8: Query by channel, hashtag, sender and date
        by_channel = repo.find_by_channel("123456789")
        assert any(m["message"]["id"] == "1001" for m in by_channel), "find_by_channel failed"
        by_hashtag = repo.find_by_hashtag("osint")
        assert any(m["message"]["id"] == "1001" for m in by_hashtag), "find_by_hashtag failed"
        by_sender = repo.find_by_sender("98765")
        assert any(m["message"]["id"] == "1001" for m in by_sender), "find_by_sender failed"
        by_keyword = repo.find_by_keyword("realistic")
        assert any(m["message"]["id"] == "1001" for m in by_keyword), "find_by_keyword failed"
        print("[OK] Query Methods Passed")

        # STEP 9: Count the total number of documents
        count = repo.count_messages()
        print(f"Current document count: {count}")

        print("[OK] Repository Test Passed (Data kept in DB for inspection)")

    except AssertionError as e:
        print(f"[FAIL] Assertion Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        sys.exit(1)
    finally:
        # STEP 10: Close the MongoDB connection
        mongodb.close()


if __name__ == "__main__":
    run_test()
