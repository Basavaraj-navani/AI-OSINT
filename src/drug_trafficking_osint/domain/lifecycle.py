"""Lifecycle states shared by the application boundary."""

from enum import StrEnum


class LifecycleState(StrEnum):
    """Valid states for the process composition root."""

    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
