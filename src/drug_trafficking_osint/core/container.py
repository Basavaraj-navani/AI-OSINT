"""Explicit dependency-injection composition root."""

from __future__ import annotations

from dataclasses import dataclass
from logging import Logger

from drug_trafficking_osint.application.runtime import ApplicationRuntime
from drug_trafficking_osint.core.config import Settings
from drug_trafficking_osint.infrastructure.logging import configure_logging


@dataclass(frozen=True, slots=True)
class Container:
    """Resolved dependencies for one process instance."""

    settings: Settings
    logger: Logger
    runtime: ApplicationRuntime


def build_container(settings: Settings | None = None) -> Container:
    """Build the production dependency graph."""
    resolved_settings = settings or Settings.from_environment()
    logger = configure_logging(resolved_settings)
    return Container(resolved_settings, logger, ApplicationRuntime(logger))
