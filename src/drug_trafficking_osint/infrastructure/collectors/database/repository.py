"""MongoDB repository implementation for the unified message schema."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, cast

from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database
from pymongo.errors import PyMongoError

from drug_trafficking_osint.infrastructure.collectors.telegram.models import (
    ChannelRef,
    ProcessingInfo,
    UnifiedMessage,
)

logger = logging.getLogger(__name__)


class Collections:
    """Names of MongoDB collections used by the platform."""

    MESSAGES = "telegram_messages"
    CHANNELS = "telegram_channels"
    USERS = "telegram_users"
    ANALYSIS = "analysis_results"
    LOGS = "system_logs"


def _normalize_iso(value: datetime | str) -> str:
    """Normalize a date filter to the UTC ISO-8601 string used in documents."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()
    return str(value)


class MongoRepository:
    """Persistence boundary for unified messages following the Repository pattern.

    The repository stores exactly one :class:`UnifiedMessage` per MongoDB
    document in ``telegram_messages``. It contains no parsing or business
    logic; emojis, hashtags, media, URLs and mentions are stored as properties
    of the message document itself.
    """

    def __init__(self, mongodb: Any) -> None:
        """Initialize the repository with an existing MongoDB connection.

        Args:
            mongodb: A PyMongo Database object, a connection manager exposing
                a ``db`` attribute, a manager exposing ``get_database()``, or a
                database-like object (e.g. a test double) to use directly.
        """
        if isinstance(mongodb, Database):
            self.db = cast("Database[dict[str, Any]]", mongodb)
        elif hasattr(mongodb, "db"):
            self.db = cast("Database[dict[str, Any]]", mongodb.db)
        elif hasattr(mongodb, "get_database"):
            self.db = cast("Database[dict[str, Any]]", mongodb.get_database())
        else:
            self.db = cast("Database[dict[str, Any]]", mongodb)
        logger.info("MongoRepository initialized with provided MongoDB connection.")

    def save_message(self, message: UnifiedMessage) -> ObjectId:
        """Insert one unified message document.

        Args:
            message: The unified message to persist.

        Returns:
            The ObjectId of the inserted document.

        Raises:
            PyMongoError: If a database error occurs.
        """
        try:
            result = self.db[Collections.MESSAGES].insert_one(message.to_dict())
            logger.debug("message_saved", extra={"object_id": str(result.inserted_id)})
            return cast(ObjectId, result.inserted_id)
        except PyMongoError as exc:
            logger.error("message_save_failed", extra={"error": str(exc)})
            raise

    def save_messages(self, messages: Sequence[UnifiedMessage]) -> list[ObjectId]:
        """Insert multiple unified message documents in one batch.

        Args:
            messages: Unified messages to persist.

        Returns:
            ObjectIds of the inserted documents (empty when input is empty).

        Raises:
            PyMongoError: If a database error occurs.
        """
        if not messages:
            return []
        try:
            documents = [message.to_dict() for message in messages]
            result = self.db[Collections.MESSAGES].insert_many(documents)
            logger.debug("messages_saved", extra={"count": len(result.inserted_ids)})
            return cast(list[ObjectId], list(result.inserted_ids))
        except PyMongoError as exc:
            logger.error("messages_save_failed", extra={"error": str(exc)})
            raise

    def save_channel(self, channel: ChannelRef | Mapping[str, Any]) -> None:
        """Insert or update a channel in ``telegram_channels``.

        Args:
            channel: Channel data containing ``channel_id`` or ``id``, or a
                :class:`ChannelRef` to persist.

        Raises:
            PyMongoError: If a database error occurs.
            ValueError: If no channel identifier is present.
        """
        if isinstance(channel, ChannelRef):
            document: dict[str, Any] = {
                "channel_id": channel.id,
                "username": channel.username,
                "title": channel.title,
                "platform": "telegram",
            }
        else:
            document = dict(channel)
        channel_id = document.get("channel_id") or document.get("id")
        if not channel_id:
            raise ValueError("Channel dictionary must contain 'channel_id' or 'id'.")
        try:
            self.db[Collections.CHANNELS].update_one(
                {"channel_id": channel_id},
                {"$set": document},
                upsert=True,
            )
            logger.debug("channel_upserted", extra={"channel_id": channel_id})
        except PyMongoError as exc:
            logger.error("channel_save_failed", extra={"channel_id": channel_id, "error": str(exc)})
            raise

    def save_user(self, user: Mapping[str, Any]) -> None:
        """Insert or update a user in ``telegram_users``.

        Args:
            user: User data containing ``user_id`` or ``id``.

        Raises:
            PyMongoError: If a database error occurs.
            ValueError: If no user identifier is present.
        """
        user_id = user.get("user_id") or user.get("id")
        if not user_id:
            raise ValueError("User dictionary must contain 'user_id' or 'id'.")
        try:
            self.db[Collections.USERS].update_one(
                {"user_id": user_id},
                {"$set": dict(user)},
                upsert=True,
            )
            logger.debug("user_upserted", extra={"user_id": user_id})
        except PyMongoError as exc:
            logger.error("user_save_failed", extra={"user_id": user_id, "error": str(exc)})
            raise

    @staticmethod
    def _message_query(message_id: str | ObjectId | int) -> dict[str, Any]:
        """Build the query locating a message by Mongo id or unified message id."""
        if isinstance(message_id, ObjectId):
            return {"_id": message_id}
        return {"message.id": str(message_id)}

    def get_message(self, message_id: str | ObjectId | int) -> dict[str, Any] | None:
        """Return one message document.

        Args:
            message_id: ``_id`` (ObjectId) or unified ``message.id``.

        Returns:
            The message document, or ``None`` if not found.
        """
        try:
            return self.db[Collections.MESSAGES].find_one(self._message_query(message_id))
        except PyMongoError as exc:
            logger.error("message_get_failed", extra={"message_id": message_id, "error": str(exc)})
            raise

    def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return message documents, optionally limited."""
        try:
            cursor = self.db[Collections.MESSAGES].find()
            if limit is not None:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as exc:
            logger.error("messages_get_failed", extra={"error": str(exc)})
            raise

    def find_by_channel(self, channel_id: str | int) -> list[dict[str, Any]]:
        """Return every message belonging to a channel.

        Args:
            channel_id: The channel identifier recorded in ``channel.id``.

        Returns:
            List of matching message documents.
        """
        try:
            cursor = self.db[Collections.MESSAGES].find({"channel.id": str(channel_id)})
            return list(cursor)
        except PyMongoError as exc:
            logger.error(
                "find_by_channel_failed", extra={"channel_id": channel_id, "error": str(exc)}
            )
            raise

    def find_by_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Search inside the unified message text (case-insensitive).

        Args:
            keyword: Plain text keyword; regex metacharacters are escaped.

        Returns:
            List of matching message documents.
        """
        escaped = re.escape(keyword)
        query = {"message.text": {"$regex": escaped, "$options": "i"}}
        try:
            return list(self.db[Collections.MESSAGES].find(query))
        except PyMongoError as exc:
            logger.error("find_by_keyword_failed", extra={"keyword": keyword, "error": str(exc)})
            raise

    def find_by_hashtag(self, hashtag: str) -> list[dict[str, Any]]:
        """Return every message containing the given hashtag.

        Args:
            hashtag: Hashtag name; a leading ``#`` is tolerated.

        Returns:
            List of matching message documents.
        """
        tag = hashtag.lstrip("#")
        try:
            return list(self.db[Collections.MESSAGES].find({"message.hashtags": tag}))
        except PyMongoError as exc:
            logger.error("find_by_hashtag_failed", extra={"hashtag": tag, "error": str(exc)})
            raise

    def find_by_sender(self, sender_id: str | int) -> list[dict[str, Any]]:
        """Return every message sent by the given user.

        Args:
            sender_id: The sender identifier recorded in ``sender.id``.

        Returns:
            List of matching message documents.
        """
        try:
            return list(self.db[Collections.MESSAGES].find({"sender.id": str(sender_id)}))
        except PyMongoError as exc:
            logger.error("find_by_sender_failed", extra={"sender_id": sender_id, "error": str(exc)})
            raise

    def find_by_date(
        self,
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> list[dict[str, Any]]:
        """Return every message within a timestamp range.

        Args:
            start_date: Inclusive range start (datetime or ISO-8601 string).
            end_date: Inclusive range end (datetime or ISO-8601 string).

        Returns:
            List of matching message documents.
        """
        query = {
            "metadata.timestamp": {
                "$gte": _normalize_iso(start_date),
                "$lte": _normalize_iso(end_date),
            }
        }
        try:
            return list(self.db[Collections.MESSAGES].find(query))
        except PyMongoError as exc:
            logger.error(
                "find_by_date_failed",
                extra={"start_date": start_date, "end_date": end_date, "error": str(exc)},
            )
            raise

    def update_processing_results(
        self,
        message_id: str | ObjectId | int,
        processing: ProcessingInfo | Mapping[str, Any],
    ) -> bool:
        """Update the nested ``processing`` sub-document of a message.

        Only the provided processing fields are overwritten via ``$set``.

        Args:
            message_id: ``_id`` (ObjectId) or unified ``message.id``.
            processing: New processing state (model or partial mapping).

        Returns:
            True if a document was modified, False otherwise.
        """
        processing_dict = (
            processing.to_dict() if isinstance(processing, ProcessingInfo) else dict(processing)
        )
        update = {f"processing.{key}": value for key, value in processing_dict.items()}
        return self.update_message(message_id, update)

    def update_message(
        self,
        message_id: str | ObjectId | int,
        update_fields: Mapping[str, Any],
    ) -> bool:
        """Update selected fields of a message document.

        Args:
            message_id: ``_id`` (ObjectId) or unified ``message.id``.
            update_fields: Dotted-path fields to set.

        Returns:
            True if a document was modified, False otherwise.
        """
        try:
            result = self.db[Collections.MESSAGES].update_one(
                self._message_query(message_id),
                {"$set": dict(update_fields)},
            )
            updated = result.modified_count > 0
            logger.debug("message_updated", extra={"message_id": message_id, "updated": updated})
            return updated
        except PyMongoError as exc:
            logger.error(
                "message_update_failed", extra={"message_id": message_id, "error": str(exc)}
            )
            raise

    def delete_message(self, message_id: str | ObjectId | int) -> bool:
        """Delete one message document."""
        try:
            result = self.db[Collections.MESSAGES].delete_one(self._message_query(message_id))
            deleted = result.deleted_count > 0
            logger.debug("message_deleted", extra={"message_id": message_id, "deleted": deleted})
            return deleted
        except PyMongoError as exc:
            logger.error(
                "message_delete_failed", extra={"message_id": message_id, "error": str(exc)}
            )
            raise

    def exists(self, message_id: str | ObjectId | int) -> bool:
        """Return True if a message document exists."""
        try:
            count = self.db[Collections.MESSAGES].count_documents(
                self._message_query(message_id), limit=1
            )
            return count > 0
        except PyMongoError as exc:
            logger.error(
                "message_exists_failed",
                extra={"message_id": message_id, "error": str(exc)},
            )
            raise

    def count_messages(self) -> int:
        """Return the total number of stored message documents."""
        try:
            return self.db[Collections.MESSAGES].estimated_document_count()
        except PyMongoError as exc:
            logger.error("messages_count_failed", extra={"error": str(exc)})
            raise

    def count_channels(self) -> int:
        """Return the number of stored channels."""
        try:
            return self.db[Collections.CHANNELS].estimated_document_count()
        except PyMongoError as exc:
            logger.error("channels_count_failed", extra={"error": str(exc)})
            raise

    def clear_collection(self, collection_name: str) -> None:
        """Delete every document from a collection (useful for testing)."""
        try:
            self.db[collection_name].delete_many({})
            logger.info("collection_cleared", extra={"collection": collection_name})
        except PyMongoError as exc:
            logger.error(
                "collection_clear_failed",
                extra={"collection": collection_name, "error": str(exc)},
            )
            raise

    def create_indexes(self) -> None:
        """Create the indexes required by the unified message schema.

        Indexes:
            - ``message.id`` unique (sparse)
            - ``channel.id``
            - ``sender.id``
            - ``metadata.timestamp``
            - ``message.hashtags``
            - ``message.mentions``
            - ``processing.risk_score``

        Raises:
            PyMongoError: If index creation fails.
        """
        try:
            messages_collection = self.db[Collections.MESSAGES]
            messages_collection.create_indexes(
                [
                    IndexModel([("message.id", ASCENDING)], unique=True, sparse=True),
                    IndexModel([("channel.id", ASCENDING)]),
                    IndexModel([("sender.id", ASCENDING)]),
                    IndexModel([("metadata.timestamp", DESCENDING)]),
                    IndexModel([("message.hashtags", ASCENDING)]),
                    IndexModel([("message.mentions", ASCENDING)]),
                    IndexModel([("processing.risk_score", ASCENDING)]),
                ]
            )
            logger.info("indexes_created", extra={"collection": Collections.MESSAGES})

            channels_collection = self.db[Collections.CHANNELS]
            channels_collection.create_index([("channel_id", ASCENDING)], unique=True, sparse=True)
            users_collection = self.db[Collections.USERS]
            users_collection.create_index([("user_id", ASCENDING)], unique=True, sparse=True)
            logger.info(
                "indexes_created",
                extra={"collections": [Collections.CHANNELS, Collections.USERS]},
            )
        except PyMongoError as exc:
            logger.error("indexes_creation_failed", extra={"error": str(exc)})
            raise
