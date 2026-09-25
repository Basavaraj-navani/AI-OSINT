import json
import logging

from drug_trafficking_osint.core.config import (
    Environment,
    LogFormat,
    MongoSettings,
    Settings,
    TelegramSettings,
)
from drug_trafficking_osint.infrastructure.logging import configure_logging
from drug_trafficking_osint.main import main


def make_settings(log_format: LogFormat) -> Settings:
    return Settings(
        Environment.TEST,
        "INFO",
        log_format,
        "test-service",
        TelegramSettings(12345, "test-hash", "test-session"),
        MongoSettings("mongodb://localhost:27017", "test"),
    )


def test_json_logging_emits_machine_readable_record(capsys) -> None:
    logger = configure_logging(make_settings(LogFormat.JSON))
    logger.info("structured event")

    record = json.loads(capsys.readouterr().out)
    assert record["message"] == "structured event"
    assert record["level"] == "INFO"


def test_json_logging_serializes_exception(capsys) -> None:
    logger = configure_logging(make_settings(LogFormat.JSON))
    logger.setLevel("ERROR")
    try:
        raise ValueError("expected test error")
    except ValueError:
        logger.exception("operation failed")

    assert "expected test error" in json.loads(capsys.readouterr().out)["exception"]


def test_entrypoint_completes(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "test-hash")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "test")
    assert main() == 0
    logging.getLogger("drug-trafficking-osint").handlers.clear()
