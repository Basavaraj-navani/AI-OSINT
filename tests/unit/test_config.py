import pytest

from drug_trafficking_osint.core.config import Environment, LogFormat, Settings


def test_settings_read_valid_environment() -> None:
    settings = Settings.from_environment(
        {
            "OSINT_ENVIRONMENT": "production",
            "OSINT_LOG_LEVEL": "warning",
            "OSINT_LOG_FORMAT": "json",
            "OSINT_SERVICE_NAME": "intelligence-core",
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "test-hash",
            "MONGODB_URI": "mongodb://localhost:27017",
            "MONGODB_DATABASE": "test",
        }
    )

    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level == "WARNING"
    assert settings.log_format is LogFormat.JSON
    assert settings.service_name == "intelligence-core"


def test_settings_reject_invalid_log_level() -> None:
    with pytest.raises(ValueError, match="OSINT_LOG_LEVEL"):
        Settings.from_environment({"OSINT_LOG_LEVEL": "verbose"})


def test_settings_reject_invalid_environment_and_empty_service_name() -> None:
    with pytest.raises(ValueError, match="OSINT_ENVIRONMENT"):
        Settings.from_environment({"OSINT_ENVIRONMENT": "staging"})
    with pytest.raises(ValueError, match="OSINT_SERVICE_NAME"):
        Settings.from_environment({"OSINT_SERVICE_NAME": "  "})
