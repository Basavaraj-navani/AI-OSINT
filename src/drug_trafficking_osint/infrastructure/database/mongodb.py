"""MongoDB connection management."""

from __future__ import annotations

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from drug_trafficking_osint.core.config import Settings

logger = logging.getLogger(__name__)


class MongoDB:
    """Manages MongoDB client lifecycle.

    This class provides a singleton-like pattern for managing
    a single MongoDB client instance across the application.

    Example:
        >>> settings = Settings.from_environment()
        >>> db = MongoDB(settings)
        >>> db.connect()
        >>> database = db.get_database()
        >>> collection = db.get_collection("messages")
        >>> db.close()
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize MongoDB manager with settings.

        Args:
            settings: Application settings containing MongoDB configuration.
        """
        self._settings = settings
        self._client: MongoClient[dict[str, Any]] | None = None
        self._database: Database[dict[str, Any]] | None = None

    def connect(self) -> MongoClient[dict[str, Any]]:
        """Create and establish MongoDB connection.

        Creates MongoClient, performs ping to verify connectivity,
        and stores the client and database references.

        Returns:
            The connected MongoClient instance.

        Raises:
            ConnectionError: If connection to MongoDB fails.
            ValueError: If MongoDB configuration is invalid.
        """
        if self._client is not None:
            logger.debug("MongoDB already connected, reusing existing connection")
            return self._client

        mongo_settings = self._settings.mongo

        if not mongo_settings.uri:
            raise ValueError("MongoDB URI is not configured")
        if not mongo_settings.database:
            raise ValueError("MongoDB database name is not configured")

        logger.info("Connecting to MongoDB at %s", mongo_settings.uri)

        try:
            self._client = MongoClient(
                mongo_settings.uri,
                maxPoolSize=mongo_settings.max_pool_size,
                minPoolSize=mongo_settings.min_pool_size,
                connectTimeoutMS=mongo_settings.connect_timeout_ms,
                serverSelectionTimeoutMS=mongo_settings.server_selection_timeout_ms,
            )

            self._client.admin.command("ping")

            self._database = self._client[mongo_settings.database]

            logger.info(
                "MongoDB connection established: database=%s, uri=%s",
                mongo_settings.database,
                mongo_settings.uri,
            )

            return self._client

        except Exception as exc:
            logger.error("Failed to connect to MongoDB: %s", exc)
            self._client = None
            self._database = None
            raise ConnectionError(f"Failed to connect to MongoDB: {exc}") from exc

    def get_database(self) -> Database[dict[str, Any]]:
        """Get the MongoDB database instance.

        Automatically connects if not already connected.

        Returns:
            The Database instance.

        Raises:
            RuntimeError: If not connected and auto-connect fails.
        """
        if self._database is None:
            self.connect()
        assert self._database is not None
        return self._database

    def get_collection(self, collection_name: str) -> Collection[dict[str, Any]]:
        """Get a MongoDB collection by name.

        Args:
            collection_name: Name of the collection to retrieve.

        Returns:
            The Collection instance.

        Raises:
            ValueError: If collection_name is empty or None.
        """
        if not collection_name or not collection_name.strip():
            raise ValueError("Collection name must not be empty")
        return self.get_database()[collection_name.strip()]

    def close(self) -> None:
        """Close the MongoDB connection and release resources."""
        if self._client is not None:
            self._client.close()
            logger.info("MongoDB connection closed")
            self._client = None
            self._database = None

    @property
    def is_connected(self) -> bool:
        """Check if MongoDB is currently connected.

        Returns:
            True if connected and responsive, False otherwise.
        """
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False
