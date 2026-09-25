"""
Custom exceptions for the AI classifier.
"""

from __future__ import annotations


class ClassifierError(Exception):
    """
    Base exception for classifier errors.
    """


class ModelLoadError(ClassifierError):
    """
    Raised when the transformer model cannot be loaded.
    """


class PredictionError(ClassifierError):
    """
    Raised when prediction fails.
    """
