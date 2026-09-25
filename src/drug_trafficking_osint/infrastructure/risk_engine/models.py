"""
Risk Engine Models
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RiskScore:
    """
    Represents the calculated risk score.
    """

    score: float
    label: str
