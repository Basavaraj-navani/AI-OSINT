import pytest

from drug_trafficking_osint.core.config import (
    Environment,
    LogFormat,
    MongoSettings,
    Settings,
    TelegramSettings,
)
from drug_trafficking_osint.core.container import build_container
from drug_trafficking_osint.domain.lifecycle import LifecycleState


def make_settings(service_name: str) -> Settings:
    return Settings(
        Environment.TEST,
        "INFO",
        LogFormat.CONSOLE,
        service_name,
        TelegramSettings(12345, "test-hash", "test-session"),
        MongoSettings("mongodb://localhost:27017", "test"),
    )


def test_container_composes_runtime() -> None:
    container = build_container(make_settings("test-service"))

    assert container.runtime.state is LifecycleState.CREATED
    container.runtime.start()
    assert container.runtime.state is LifecycleState.RUNNING
    container.runtime.stop()
    assert container.runtime.state is LifecycleState.STOPPED


def test_runtime_rejects_invalid_state_transitions() -> None:
    container = build_container(make_settings("test-service-invalid"))
    with pytest.raises(RuntimeError, match="Cannot stop"):
        container.runtime.stop()
    container.runtime.start()
    with pytest.raises(RuntimeError, match="Cannot start"):
        container.runtime.start()
