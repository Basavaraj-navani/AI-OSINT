"""Small pure helpers shared by preprocessing stages."""

from __future__ import annotations

from collections.abc import Mapping

from drug_trafficking_osint.infrastructure.nlp.exceptions import InvalidConfigurationError


def read_bool(values: Mapping[str, str], key: str, default: bool) -> bool:
    """Read a strict boolean from environment-like values.

    Args:
        values: Mapping containing optional configuration values.
        key: Name of the setting to read.
        default: Value used when ``key`` is absent.

    Raises:
        InvalidConfigurationError: If a supplied value is not a boolean literal.
    """
    value = values.get(key)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise InvalidConfigurationError(f"{key} must be a boolean literal")


def read_positive_int(values: Mapping[str, str], key: str, default: int) -> int:
    """Read a positive integer setting, rejecting malformed or non-positive values."""
    value = values.get(key)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise InvalidConfigurationError(f"{key} must be an integer") from error
    if parsed < 1:
        raise InvalidConfigurationError(f"{key} must be greater than zero")
    return parsed


def read_csv(values: Mapping[str, str], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Read a normalized, non-empty comma-separated language list."""
    value = values.get(key)
    if value is None:
        return default
    result = tuple(item.strip().lower() for item in value.split(",") if item.strip())
    if not result:
        raise InvalidConfigurationError(f"{key} must contain at least one value")
    return result
