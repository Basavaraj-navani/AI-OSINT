"""Unit tests for the unified message schema, parser, repository, exporter and media pipeline."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock

import pytest
from bson.objectid import ObjectId
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
)

from drug_trafficking_osint.infrastructure.collectors.database.repository import (
    Collections,
    MongoRepository,
)
from drug_trafficking_osint.infrastructure.collectors.storage.exporter import (
    ExportFormat,
    UnifiedMessageExporter,
)
from drug_trafficking_osint.infrastructure.collectors.telegram import (
    TelegramCollector,
    TelegramParser,
)
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

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def build_unified() -> UnifiedMessage:
    """Return a representative unified message matching the schema."""
    return UnifiedMessage(
        platform="telegram",
        channel=ChannelRef(id="123456789", username="my_channel", title="My Channel"),
        sender=SenderRef(id="987", username="dealer", display_name="John Doe"),
        message=MessageContent(
            id="42",
            text="Check out #crypto @john https://example.com 🚀💊",
            hashtags=["crypto"],
            mentions=["john"],
            urls=["https://example.com"],
            emojis=["🚀", "💊"],
        ),
        media=MediaInfo(has_media=False),
        metadata=MessageMetadata(
            timestamp="2026-07-31T12:00:00+00:00", views=1500, forwards=30, reply_count=12
        ),
        processing=ProcessingInfo(),
    )


def make_telethon_message(
    message_id: int = 42, text: str | None = "Hello #world @user", media: Any = None
) -> Any:
    """Build a lightweight Telethon-like message for parser tests."""
    chat = SimpleNamespace(id=123456789, username="my_channel", title="My Channel")
    sender = SimpleNamespace(id=987, username="dealer", first_name="John", last_name="Doe")
    return SimpleNamespace(
        id=message_id,
        chat=chat,
        chat_id=-100123456789,
        sender=sender,
        sender_id=987,
        text=text,
        date=datetime(2026, 7, 31, 12, 0, 0, tzinfo=UTC),
        edit_date=None,
        views=1500,
        forwards=30,
        replies=SimpleNamespace(replies=12),
        media=media,
    )


def make_fake_db() -> tuple[mock.MagicMock, mock.MagicMock]:
    """Return a ``(db, collection)`` mock pair backed by a fake collection."""

    class FakeDatabase:
        """Plain dict-like DB so MongoRepository does not sniff a ``.db`` attr."""

        def __init__(self, collection: mock.MagicMock) -> None:
            self._collection = collection

        def __getitem__(self, name: str) -> mock.MagicMock:
            return self._collection

    collection = mock.MagicMock()
    collection.insert_one.return_value.inserted_id = ObjectId("64b64b64b64b64b64b64b64b")
    collection.update_one.return_value.modified_count = 1
    collection.delete_one.return_value.deleted_count = 1
    return FakeDatabase(collection), collection


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestUnifiedSchema:
    def test_to_dict_matches_required_schema(self) -> None:
        document = build_unified().to_dict()

        assert set(document) == {
            "platform",
            "channel",
            "sender",
            "message",
            "media",
            "metadata",
            "processing",
        }
        assert set(document["channel"]) == {"id", "username", "title"}
        assert set(document["sender"]) == {"id", "username", "display_name"}
        assert set(document["message"]) == {
            "id",
            "text",
            "clean_text",
            "hashtags",
            "mentions",
            "urls",
            "emojis",
            "language",
        }
        assert set(document["media"]) == {
            "has_media",
            "type",
            "telegram_file_id",
            "filename",
            "mime_type",
            "width",
            "height",
            "duration",
            "size_bytes",
            "local_path",
            "hash",
        }
        assert set(document["metadata"]) == {
            "timestamp",
            "views",
            "forwards",
            "reply_count",
            "edit_date",
        }
        assert set(document["processing"]) == {
            "nlp_completed",
            "ner_completed",
            "graph_completed",
            "risk_score",
            "classification",
            "entities",
        }

    def test_empty_message_serializes_full_schema_with_nulls(self) -> None:
        document = UnifiedMessage(platform="telegram").to_dict()
        assert document["channel"] == {"id": None, "username": None, "title": None}
        assert document["media"]["has_media"] is False
        assert document["metadata"]["views"] == 0
        assert document["processing"]["nlp_completed"] is False
        assert document["message"]["emojis"] == []

    def test_from_dict_round_trip(self) -> None:
        message = build_unified()
        restored = UnifiedMessage.from_dict(message.to_dict())
        assert restored == message

    def test_from_dict_ignores_mongodb_id(self) -> None:
        document = build_unified().to_dict()
        document["_id"] = ObjectId()
        restored = UnifiedMessage.from_dict(document)
        assert restored == build_unified()

    def test_platform_can_change_without_affecting_schema(self) -> None:
        document = UnifiedMessage(platform="instagram", message=MessageContent(id="XZ_1")).to_dict()
        assert document["platform"] == "instagram"
        assert document["message"]["id"] == "XZ_1"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class TestParser:
    def test_parse_text_message_extracts_full_schema(self) -> None:
        parsed = TelegramParser().parse(make_telethon_message())

        assert parsed.platform == "telegram"
        assert parsed.channel.id == "123456789"
        assert parsed.channel.username == "my_channel"
        assert parsed.channel.title == "My Channel"
        assert parsed.sender.id == "987"
        assert parsed.sender.username == "dealer"
        assert parsed.sender.display_name == "John Doe"

        assert parsed.message.id == "42"
        assert parsed.message.text == "Hello #world @user"
        assert parsed.message.clean_text is None
        assert parsed.message.hashtags == ["world"]
        assert parsed.message.mentions == ["user"]
        assert parsed.message.urls == []
        assert parsed.message.language is None

        assert parsed.metadata.timestamp == "2026-07-31T12:00:00+00:00"
        assert parsed.metadata.views == 1500
        assert parsed.metadata.forwards == 30
        assert parsed.metadata.reply_count == 12
        assert parsed.metadata.edit_date is None

        assert parsed.media.has_media is False
        assert parsed.processing.nlp_completed is False

    def test_parse_extracts_emojis(self) -> None:
        parsed = TelegramParser().parse(make_telethon_message(text="🚀💊💊 good job 👍"))
        assert "🚀" in parsed.message.emojis
        assert parsed.message.emojis.count("💊") == 2
        assert "👍" in parsed.message.emojis

    def test_parse_missing_sender_and_views(self) -> None:
        message = make_telethon_message()
        message.sender = None
        message.sender_id = None
        message.views = None
        message.forwards = None
        message.replies = None

        parsed = TelegramParser().parse(message)
        assert parsed.sender.id is None
        assert parsed.sender.display_name is None
        assert parsed.metadata.views == 0
        assert parsed.metadata.forwards == 0
        assert parsed.metadata.reply_count == 0

    def test_parse_photo_media(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import drug_trafficking_osint.infrastructure.collectors.telegram.parser as parser_module

        class FakePhotoMedia:
            pass

        monkeypatch.setattr(parser_module, "TELETHON_MESSAGE_MEDIA_PHOTO", FakePhotoMedia)
        fake_media = FakePhotoMedia()
        fake_media.photo = SimpleNamespace(
            id=777, sizes=[SimpleNamespace(w=1280, h=720), SimpleNamespace(w=100, h=100)]
        )

        parsed = TelegramParser().parse(make_telethon_message(media=fake_media))
        assert parsed.media.has_media is True
        assert parsed.media.type == "photo"
        assert parsed.media.telegram_file_id == "777"
        assert parsed.media.width == 1280
        assert parsed.media.height == 720

    def test_parse_document_media(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import drug_trafficking_osint.infrastructure.collectors.telegram.parser as parser_module

        class FakeDocumentMedia:
            pass

        monkeypatch.setattr(parser_module, "TELETHON_MESSAGE_MEDIA_DOCUMENT", FakeDocumentMedia)
        fake_media = FakeDocumentMedia()
        fake_media.document = SimpleNamespace(
            id=888,
            mime_type="video/mp4",
            size=2048,
            thumb=None,
            attributes=[
                DocumentAttributeFilename(file_name="clip.mp4"),
                DocumentAttributeVideo(w=640, h=360, duration=15),
            ],
        )

        parsed = TelegramParser().parse(make_telethon_message(media=fake_media))
        assert parsed.media.has_media is True
        assert parsed.media.type == "video"
        assert parsed.media.telegram_file_id == "888"
        assert parsed.media.filename == "clip.mp4"
        assert parsed.media.mime_type == "video/mp4"
        assert parsed.media.width == 640
        assert parsed.media.height == 360
        assert parsed.media.duration == 15
        assert parsed.media.size_bytes == 2048

    def test_parse_batch(self) -> None:
        parsed = TelegramParser().parse_batch(
            [make_telethon_message(message_id=1), make_telethon_message(message_id=2)]
        )
        assert [msg.message.id for msg in parsed] == ["1", "2"]


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class TestRepository:
    def test_save_message_inserts_schema_document(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)
        message = build_unified()

        inserted_id = repo.save_message(message)

        assert inserted_id == ObjectId("64b64b64b64b64b64b64b64b")
        collection.insert_one.assert_called_once_with(message.to_dict())

    def test_save_messages_batches_documents(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)
        messages = [build_unified(), build_unified()]

        repo.save_messages(messages)

        collection.insert_many.assert_called_once_with([m.to_dict() for m in messages])

    def test_save_messages_empty_returns_without_db_call(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)
        assert repo.save_messages([]) == []
        collection.insert_many.assert_not_called()

    def test_find_by_channel_uses_nested_query(self) -> None:
        db, collection = make_fake_db()
        collection.find.return_value = [build_unified().to_dict()]
        repo = MongoRepository(db)

        results = repo.find_by_channel("123456789")

        collection.find.assert_called_once_with({"channel.id": "123456789"})
        assert results[0]["channel"]["id"] == "123456789"

    def test_find_by_keyword_escapes_and_searches_message_text(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.find_by_keyword("drugs (street)")

        query = collection.find.call_args.args[0]
        assert query["message.text"]["$options"] == "i"
        assert query["message.text"]["$regex"] == re.escape("drugs (street)")

    def test_find_by_hashtag_strips_prefix(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.find_by_hashtag("#crypto")

        collection.find.assert_called_once_with({"message.hashtags": "crypto"})

    def test_find_by_sender_uses_nested_query(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.find_by_sender(987)

        collection.find.assert_called_once_with({"sender.id": "987"})

    def test_find_by_date_normalizes_to_iso(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.find_by_date(
            datetime(2026, 7, 1, tzinfo=UTC),
            datetime(2026, 7, 31, 23, 59, tzinfo=UTC),
        )

        collection.find.assert_called_once_with(
            {
                "metadata.timestamp": {
                    "$gte": "2026-07-01T00:00:00+00:00",
                    "$lte": "2026-07-31T23:59:00+00:00",
                }
            }
        )

    def test_update_processing_results_sets_nested_fields(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        updated = repo.update_processing_results(
            "42",
            ProcessingInfo(nlp_completed=True, risk_score=0.85, classification="high_risk"),
        )

        assert updated is True
        collection.update_one.assert_called_once_with(
            {"message.id": "42"},
            {
                "$set": {
                    "processing.nlp_completed": True,
                    "processing.ner_completed": False,
                    "processing.graph_completed": False,
                    "processing.risk_score": 0.85,
                    "processing.classification": "high_risk",
                    "processing.entities": [],
                }
            },
        )

    def test_update_processing_results_accepts_partial_mapping(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.update_processing_results("42", {"risk_score": 0.9})

        collection.update_one.assert_called_once_with(
            {"message.id": "42"}, {"$set": {"processing.risk_score": 0.9}}
        )

    def test_get_message_queries_by_object_id(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)
        object_id = ObjectId()

        repo.get_message(object_id)

        collection.find_one.assert_called_once_with({"_id": object_id})

    def test_create_indexes_creates_required_indexes(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.create_indexes()

        assert collection.create_indexes.call_count == 1
        index_models = collection.create_indexes.call_args.args[0]
        specs = [model.document["key"] for model in index_models]
        assert {"message.id": 1} in specs
        assert {"channel.id": 1} in specs
        assert {"sender.id": 1} in specs
        assert {"metadata.timestamp": -1} in specs
        assert {"message.hashtags": 1} in specs
        assert {"message.mentions": 1} in specs
        assert {"processing.risk_score": 1} in specs

    def test_collection_names(self) -> None:
        assert Collections.MESSAGES == "telegram_messages"
        assert Collections.CHANNELS == "telegram_channels"
        assert Collections.USERS == "telegram_users"
        assert Collections.ANALYSIS == "analysis_results"
        assert Collections.LOGS == "system_logs"

    def test_save_channel_and_user_upsert(self) -> None:
        db, collection = make_fake_db()
        repo = MongoRepository(db)

        repo.save_channel({"channel_id": "1", "title": "Channel"})
        repo.save_user({"user_id": "2", "username": "user"})

        assert collection.update_one.call_count == 2


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------


class TestExporter:
    def test_export_json(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        path = tmp_path / "messages.json"

        exporter.export([build_unified()], path, ExportFormat.JSON)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data[0]["platform"] == "telegram"
        assert data[0]["channel"]["id"] == "123456789"
        assert data[0]["message"]["hashtags"] == ["crypto"]

    def test_export_jsonl(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        path = tmp_path / "messages.jsonl"

        exporter.export_jsonl([build_unified(), build_unified()], path)

        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
        assert len(lines) == 2
        assert json.loads(lines[0])["message"]["id"] == "42"

    def test_export_csv_flattens_nested_document(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        path = tmp_path / "messages.csv"

        exporter.export_csv([build_unified()], path)

        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["channel.id"] == "123456789"
        assert rows[0]["sender.username"] == "dealer"
        assert rows[0]["metadata.views"] == "1500"
        assert rows[0]["message.hashtags"] == '["crypto"]'

    def test_export_csv_empty_messages_creates_empty_file(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        path = tmp_path / "empty.csv"

        exporter.export_csv([], path)

        assert path.read_text(encoding="utf-8") == ""

    def test_export_mongodb_document_with_object_id(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        path = tmp_path / "db.json"
        document = build_unified().to_dict()
        document["_id"] = ObjectId("64b64b64b64b64b64b64b64b")

        exporter.export([document], path, "json")

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data[0]["_id"] == "64b64b64b64b64b64b64b64b"

    def test_export_rejects_unsupported_format(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        with pytest.raises(ValueError):
            exporter.export([build_unified()], tmp_path / "out.txt", "xml")

    def test_export_rejects_raw_telethon_objects(self, tmp_path: Path) -> None:
        exporter = UnifiedMessageExporter()
        with pytest.raises(TypeError):
            exporter.export([object()], tmp_path / "out.json", "json")


# ---------------------------------------------------------------------------
# Media downloader
# ---------------------------------------------------------------------------


class TestMediaDownloader:
    def test_download_writes_bytes_and_returns_local_path_and_hash(self, tmp_path: Path) -> None:
        class FakeClient:
            async def download_media(self, message, file=None):
                Path(file).write_bytes(b"media-bytes")
                return file

        downloader = TelegramMediaDownloader(tmp_path)
        message = SimpleNamespace(id=42)
        media = MediaInfo(has_media=True, type="photo", mime_type="image/jpeg")

        result = asyncio.run(downloader.download(FakeClient(), message, media))

        assert result is not None
        assert result.local_path == (tmp_path / "42.jpg").as_posix()
        assert result.sha256 == hashlib.sha256(b"media-bytes").hexdigest()

    def test_download_no_media_returns_none(self, tmp_path: Path) -> None:
        downloader = TelegramMediaDownloader(tmp_path)
        result = asyncio.run(
            downloader.download(SimpleNamespace(), SimpleNamespace(id=1), MediaInfo())
        )
        assert result is None

    def test_download_failure_returns_none(self, tmp_path: Path) -> None:
        class FailingClient:
            async def download_media(self, message, file=None):
                return None

        downloader = TelegramMediaDownloader(tmp_path)
        media = MediaInfo(has_media=True, type="photo", mime_type="image/jpeg")
        result = asyncio.run(downloader.download(FailingClient(), SimpleNamespace(id=7), media))
        assert result is None


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class TestCollector:
    def test_collector_parses_yields_and_persists_via_sink(self) -> None:
        class RecordingSink:
            def __init__(self) -> None:
                self.saved: list[UnifiedMessage] = []
                self.saved_channels: list[Any] = []

            def save_message(self, message: UnifiedMessage) -> object:
                self.saved.append(message)
                return object()

            def save_channel(self, channel: Any) -> None:
                self.saved_channels.append(channel)

        class FakeTelethonClient:
            def __init__(self, messages: list[Any]) -> None:
                self._messages = messages

            async def get_entity(self, channel: str) -> object:
                return object()

            def iter_messages(self, entity: object, limit: int = 100) -> Any:
                async def generator():
                    for message in self._messages[:limit]:
                        yield message

                return generator()

        class FakeClientWrapper:
            def __init__(self, messages: list[Any]) -> None:
                self._telethon = FakeTelethonClient(messages)

            def get_client(self) -> FakeTelethonClient:
                return self._telethon

        async def collect(collector: TelegramCollector) -> list[UnifiedMessage]:
            return [msg async for msg in collector.collect_channel("my_channel")]

        sink = RecordingSink()
        messages = [make_telethon_message(message_id=1), make_telethon_message(message_id=2)]
        collector = TelegramCollector(FakeClientWrapper(messages), sink=sink)

        collected = asyncio.run(collect(collector))

        assert [msg.message.id for msg in collected] == ["1", "2"]
        assert [msg.message.id for msg in sink.saved] == ["1", "2"]

    def test_collector_attach_media_updates_local_path_and_hash(self, tmp_path: Path) -> None:
        class FakeClient:
            async def download_media(self, message, file=None):
                Path(file).write_bytes(b"bytes")
                return file

        async def attach(collector: TelegramCollector) -> UnifiedMessage:
            message = make_telethon_message(message_id=5)
            parsed = UnifiedMessage(
                platform="telegram",
                message=MessageContent(id="5", text="media"),
                media=MediaInfo(has_media=True, type="photo", mime_type="image/jpeg"),
            )
            return await collector._attach_media(FakeClient(), message, parsed)

        collector = TelegramCollector(object(), media_dir=tmp_path)
        result = asyncio.run(attach(collector))

        assert result.media.local_path == (tmp_path / "5.jpg").as_posix()
        assert result.media.hash == hashlib.sha256(b"bytes").hexdigest()
