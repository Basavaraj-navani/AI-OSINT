"""
Database Models
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AnalysisRecord:
    """
    Represents a stored analysis record.
    """

    text: str
    risk_score: float
    risk_label: str
    created_at: datetime
