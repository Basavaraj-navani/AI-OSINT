"""Minimal application lifecycle used by the executable composition root."""

from __future__ import annotations

import logging

from drug_trafficking_osint.domain.lifecycle import LifecycleState


class ApplicationRuntime:
    """Own application lifecycle transitions without embedding delivery concerns."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._state = LifecycleState.CREATED

    @property
    def state(self) -> LifecycleState:
        """Return the current lifecycle state."""
        return self._state

    def start(self) -> None:
        """Move from created to running exactly once."""
        if self._state is not LifecycleState.CREATED:
            raise RuntimeError(f"Cannot start application from state {self._state}")
        self._state = LifecycleState.RUNNING
        self._logger.info("Application foundation started")

    def stop(self) -> None:
        """Stop a running application and record its controlled shutdown."""
        if self._state is not LifecycleState.RUNNING:
            raise RuntimeError(f"Cannot stop application from state {self._state}")
        self._state = LifecycleState.STOPPED
        self._logger.info("Application foundation stopped")
