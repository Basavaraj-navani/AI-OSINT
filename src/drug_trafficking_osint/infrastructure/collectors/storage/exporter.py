"""Export unified message documents to JSON, CSV, or JSONL."""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from bson.objectid import ObjectId

from drug_trafficking_osint.infrastructure.collectors.telegram.models import UnifiedMessage

logger = logging.getLogger(__name__)


class ExportFormat(StrEnum):
    """Supported output formats for unified message exports."""

    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"


def _json_default(value: Any) -> Any:
    """Convert non-JSON MongoDB values into portable primitives."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class UnifiedMessageExporter:
    """Serialize unified messages into portable files.

    Only :class:`UnifiedMessage` objects (or their dictionary form) are
    exported; raw Telethon objects are never accepted.
    """

    def export(
        self,
        messages: Sequence[UnifiedMessage | Mapping[str, Any]],
        path: str | Path,
        export_format: ExportFormat | str,
    ) -> None:
        """Export messages in the requested format.

        Args:
            messages: Unified messages (or documents) to export.
            path: Destination file path.
            export_format: One of ``json``, ``csv``, ``jsonl``.

        Raises:
            ValueError: If the format is unsupported.
        """
        fmt = ExportFormat(export_format)
        if fmt is ExportFormat.JSON:
            self.export_json(messages, path)
        elif fmt is ExportFormat.CSV:
            self.export_csv(messages, path)
        else:
            self.export_jsonl(messages, path)

    def export_json(
        self,
        messages: Sequence[UnifiedMessage | Mapping[str, Any]],
        path: str | Path,
    ) -> None:
        """Export messages as a JSON array of unified documents."""
        documents = [self._as_document(message) for message in messages]
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            json.dump(documents, handle, default=_json_default, ensure_ascii=False, indent=2)
        self._log_export("json", documents, destination)

    def export_jsonl(
        self,
        messages: Sequence[UnifiedMessage | Mapping[str, Any]],
        path: str | Path,
    ) -> None:
        """Export messages as JSON Lines (one unified document per line)."""
        documents = [self._as_document(message) for message in messages]
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for document in documents:
                handle.write(json.dumps(document, default=_json_default, ensure_ascii=False) + "\n")
        self._log_export("jsonl", documents, destination)

    def export_csv(
        self,
        messages: Sequence[UnifiedMessage | Mapping[str, Any]],
        path: str | Path,
    ) -> None:
        """Export messages as CSV with one row per message.

        Nested sub-documents are flattened to dot-notation columns (e.g.
        ``channel.id``); list values are serialized as JSON strings.
        """
        documents = [self._flatten(self._as_document(message)) for message in messages]
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if not documents:
            destination.write_text("", encoding="utf-8")
            logger.warning("export_empty", extra={"format": "csv", "path": str(destination)})
            return

        columns = list(dict.fromkeys(key for document in documents for key in document))
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for document in documents:
                row = {key: self._csv_value(document.get(key)) for key in columns}
                writer.writerow(row)
        self._log_export("csv", documents, destination)

    @staticmethod
    def _as_document(message: UnifiedMessage | Mapping[str, Any]) -> dict[str, Any]:
        """Normalize a unified message (or document) into a plain dictionary."""
        if isinstance(message, UnifiedMessage):
            return message.to_dict()
        if isinstance(message, Mapping):
            return dict(message)
        raise TypeError(
            f"Only UnifiedMessage objects or mappings are supported, got {type(message).__name__}"
        )

    @staticmethod
    def _flatten(document: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten a nested document into dot-notation keys."""
        flattened: dict[str, Any] = {}
        for key, value in document.items():
            dotted = f"{prefix}.{key}" if prefix else key
            if isinstance(value, Mapping):
                flattened.update(UnifiedMessageExporter._flatten(value, dotted))
            elif isinstance(value, (list, tuple)):
                flattened[dotted] = json.dumps(value, default=_json_default, ensure_ascii=False)
            else:
                flattened[dotted] = value
        return flattened

    @staticmethod
    def _csv_value(value: Any) -> Any:
        """Convert ``None`` values to empty strings for CSV output."""
        return "" if value is None else value

    @staticmethod
    def _log_export(fmt: str, documents: list[dict[str, Any]], destination: Path) -> None:
        """Emit a structured log line for a completed export."""
        logger.info(
            "export_completed",
            extra={"format": fmt, "count": len(documents), "path": str(destination)},
        )
