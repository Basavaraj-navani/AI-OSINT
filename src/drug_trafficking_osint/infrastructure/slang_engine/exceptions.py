"""
Custom exceptions for the Drug Slang Intelligence Engine.
"""

from __future__ import annotations


class SlangEngineError(Exception):
    """Base exception for the slang engine."""


class DictionaryLoadError(SlangEngineError):
    """Raised when the slang dictionary cannot be loaded."""


class InvalidDictionaryError(SlangEngineError):
    """Raised when the slang dictionary contains invalid data."""
