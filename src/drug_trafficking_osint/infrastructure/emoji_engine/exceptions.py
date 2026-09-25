"""
Custom exceptions for the Emoji Intelligence Engine.
"""

from __future__ import annotations


class EmojiEngineError(Exception):
    """
    Base exception for the emoji engine.
    """


class DictionaryLoadError(EmojiEngineError):
    """
    Raised when the emoji dictionary cannot be loaded.
    """


class InvalidDictionaryError(EmojiEngineError):
    """
    Raised when the emoji dictionary has an invalid format.
    """
