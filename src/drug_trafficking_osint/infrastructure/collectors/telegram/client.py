"""Telegram client wrapper for Telethon connection management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

from drug_trafficking_osint.core.config import Settings
from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TelethonClient,
    telethon_auth_error_type,
    telethon_client_type,
)


@dataclass(frozen=True, slots=True)
class TelegramClientConfig:
    """Configuration for the Telegram client."""

    api_id: int
    api_hash: str
    session_name: str
    session_dir: Path


class TelegramClient:
    """Wrapper around Telethon client for connection lifecycle management."""

    def __init__(self, settings: Settings) -> None:
        self._config = TelegramClientConfig(
            api_id=settings.telegram.api_id,
            api_hash=settings.telegram.api_hash,
            session_name=settings.telegram.session_name,
            session_dir=Path.cwd() / "sessions",
        )
        self._client: TelethonClient | None = None
        self._connected = False

    def _create_client(self) -> TelethonClient:
        """Create a new Telethon client instance."""
        self._config.session_dir.mkdir(parents=True, exist_ok=True)
        session_path = self._config.session_dir / self._config.session_name

        return telethon_client_type()(
            session=str(session_path),
            api_id=self._config.api_id,
            api_hash=self._config.api_hash,
        )

    async def connect(self) -> None:
        """Connect to Telegram and authenticate if needed."""
        if self._connected and self._client and self._client.is_connected():
            return

        client = self._create_client()
        self._client = client

        try:
            await client.connect()
        except telethon_auth_error_type():
            # Session invalid, recreate
            client = self._create_client()
            self._client = client
            await client.connect()

        if not await client.is_user_authorized():
            # First run - requires interactive auth
            # In production, this would be handled differently
            raise RuntimeError(
                "Telegram client not authorized. " "Run interactive authentication first."
            )

        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from Telegram cleanly."""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        """Check if client is connected and authorized."""
        return self._connected and self._client is not None and self._client.is_connected()

    def get_client(self) -> TelethonClient | None:
        """Get the underlying Telethon client."""
        return self._client

    async def ensure_connected(self) -> TelethonClient:
        """Ensure client is connected, return it."""
        if not self.is_connected():
            await self.connect()
        assert self._client is not None
        return self._client

    async def __aenter__(self) -> TelegramClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.disconnect()
