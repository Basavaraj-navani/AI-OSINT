"""
Risk Engine Exceptions
"""

from __future__ import annotations


class RiskEngineError(Exception):
    """
    Base exception for the Risk Engine.
    """


class InvalidRiskScoreError(RiskEngineError):
    """
    Raised when an invalid risk score is calculated.
    """
