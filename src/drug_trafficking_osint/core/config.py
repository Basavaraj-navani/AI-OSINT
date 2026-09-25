"""Typed configuration loaded from the process environment."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv


class Environment(StrEnum):
    """Deployment environments supported by the foundation."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    """Log encodings supported by the logging adapter."""

    CONSOLE = "console"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class TelegramSettings:
    """Telegram API configuration."""

    api_id: int
    api_hash: str
    session_name: str


@dataclass(frozen=True, slots=True)
class MongoSettings:
    """MongoDB connection configuration."""

    uri: str
    database: str
    max_pool_size: int = 100
    min_pool_size: int = 0
    connect_timeout_ms: int = 10000
    server_selection_timeout_ms: int = 10000


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated, immutable process settings."""

    environment: Environment
    log_level: str
    log_format: LogFormat
    service_name: str
    telegram: TelegramSettings
    mongo: MongoSettings

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build settings from an environment mapping, failing early if invalid."""
        load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env", override=False)
        values = os.environ if environ is None else environ
        environment = _as_enum(
            Environment,
            values.get("OSINT_ENVIRONMENT", Environment.DEVELOPMENT),
            "OSINT_ENVIRONMENT",
        )
        log_format = _as_enum(
            LogFormat, values.get("OSINT_LOG_FORMAT", LogFormat.CONSOLE), "OSINT_LOG_FORMAT"
        )
        log_level = values.get("OSINT_LOG_LEVEL", "INFO").upper()
        if log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            msg = "OSINT_LOG_LEVEL must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG"
            raise ValueError(msg)
        service_name = values.get("OSINT_SERVICE_NAME", "drug-trafficking-osint").strip()
        if not service_name:
            msg = "OSINT_SERVICE_NAME must not be empty"
            raise ValueError(msg)

        telegram_api_id = values.get("TELEGRAM_API_ID")
        if not telegram_api_id:
            msg = "TELEGRAM_API_ID must be set"
            raise ValueError(msg)
        telegram_api_hash = values.get("TELEGRAM_API_HASH")
        if not telegram_api_hash:
            msg = "TELEGRAM_API_HASH must be set"
            raise ValueError(msg)
        telegram_session_name = values.get("TELEGRAM_SESSION_NAME", "osint_session").strip()
        if not telegram_session_name:
            msg = "TELEGRAM_SESSION_NAME must not be empty"
            raise ValueError(msg)

        mongo_uri = values.get("MONGODB_URI", "mongodb://localhost:27017")
        mongo_database = values.get("MONGODB_DATABASE", "osint")
        mongo_max_pool = int(values.get("MONGODB_MAX_POOL_SIZE", "100"))
        mongo_min_pool = int(values.get("MONGODB_MIN_POOL_SIZE", "0"))
        mongo_connect_timeout = int(values.get("MONGODB_CONNECT_TIMEOUT_MS", "10000"))
        mongo_server_timeout = int(values.get("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "10000"))

        telegram = TelegramSettings(
            api_id=int(telegram_api_id),
            api_hash=telegram_api_hash,
            session_name=telegram_session_name,
        )
        mongo = MongoSettings(
            uri=mongo_uri,
            database=mongo_database,
            max_pool_size=mongo_max_pool,
            min_pool_size=mongo_min_pool,
            connect_timeout_ms=mongo_connect_timeout,
            server_selection_timeout_ms=mongo_server_timeout,
        )

        return cls(environment, log_level, log_format, service_name, telegram, mongo)


def _as_enum[EnumT: StrEnum](enum_type: type[EnumT], value: str, key: str) -> EnumT:
    try:
        return enum_type(value.lower())
    except ValueError as error:
        allowed = ", ".join(member.value for member in enum_type)
        raise ValueError(f"{key} must be one of: {allowed}") from error
