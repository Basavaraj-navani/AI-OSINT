"""Structured logging adapter implemented with the standard library."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from drug_trafficking_osint.core.config import LogFormat, Settings


class JsonFormatter(logging.Formatter):
    """Render log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        standard_fields = set(logging.makeLogRecord({}).__dict__)
        context = {
            key: value for key, value in record.__dict__.items() if key not in standard_fields
        }
        if context:
            payload["context"] = context
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure the application's dedicated logger without mutating root logging."""
    logger = logging.getLogger(settings.service_name)
    logger.setLevel(settings.log_level)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter()
        if settings.log_format is LogFormat.JSON
        else logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger
