"""
Data models for the AI classifier.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """
    Result returned by the AI classifier.
    """

    label: str
    confidence: float
