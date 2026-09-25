"""
Custom exceptions for the Named Entity Recognition engine.
"""

from __future__ import annotations


class NEREngineError(Exception):
    """
    Base exception for all NER engine errors.
    """


class ModelLoadError(NEREngineError):
    """
    Raised when the spaCy model cannot be loaded.
    """
