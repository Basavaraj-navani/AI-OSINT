"""Download Telegram media to disk, storing only the local path in MongoDB."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TelethonClient,
    TelethonMessage,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.models import MediaInfo

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DownloadedMedia:
    """Result of a successful media download."""

    local_path: str
    sha256: str | None


class TelegramMediaDownloader:
    """Persist Telegram media bytes on the local filesystem.

    Media bytes are never written to MongoDB; only ``media.local_path`` and the
    content ``hash`` are stored. Downloads land under ``datasets/media/telegram/``
    by default so the pipeline stays consistent with the unified schema.
    """

    _EXTENSIONS: ClassVar[dict[str, str]] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
    }
    _TYPE_FALLBACKS: ClassVar[dict[str, str]] = {
        "photo": ".jpg",
        "image": ".jpg",
        "video": ".mp4",
        "audio": ".m4a",
        "animation": ".gif",
        "sticker": ".webp",
        "document": ".bin",
    }

    def __init__(self, media_dir: str | Path = "datasets/media/telegram") -> None:
        """Initialize the downloader with a destination directory.

        Args:
            media_dir: Directory where media bytes are stored.
        """
        self._media_dir = Path(media_dir)

    @property
    def media_dir(self) -> Path:
        """Return the configured media directory."""
        return self._media_dir

    async def download(
        self,
        client: TelethonClient,
        message: TelethonMessage,
        media: MediaInfo,
    ) -> DownloadedMedia | None:
        """Download the message media if present and computable.

        Args:
            client: Connected Telethon client used to download bytes.
            message: Telethon message holding the media.
            media: Parsed media metadata (must have ``has_media`` set).

        Returns:
            A :class:`DownloadedMedia` result or ``None`` when the message has
            no downloadable media or the download fails.
        """
        if not media.has_media:
            return None
        if media.type not in {
            "photo",
            "video",
            "audio",
            "image",
            "animation",
            "sticker",
            "document",
        }:
            logger.debug("media_type_not_downloadable", extra={"type": media.type})
            return None

        target = self._build_target(message, media)
        target.parent.mkdir(parents=True, exist_ok=True)

        result = await client.download_media(message, file=str(target))
        if result is None:
            logger.warning("media_download_failed", extra={"message_id": message.id})
            return None
        if not target.is_file():
            logger.warning("media_download_missing", extra={"path": str(target)})
            return None

        return DownloadedMedia(local_path=self._to_local_path(target), sha256=self._sha256(target))

    def _build_target(self, message: TelethonMessage, media: MediaInfo) -> Path:
        """Build the destination path from the message id and media type."""
        extension = self._EXTENSIONS.get(media.mime_type) if media.mime_type else None
        if extension is None:
            extension = self._TYPE_FALLBACKS.get(media.type or "", ".bin")
        return self._media_dir / f"{message.id}{extension}"

    @staticmethod
    def _to_local_path(target: Path) -> str:
        """Return the portable POSIX path recorded inside MongoDB."""
        return target.as_posix()

    @staticmethod
    def _sha256(path: Path) -> str:
        """Compute the SHA-256 digest of a downloaded file."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
