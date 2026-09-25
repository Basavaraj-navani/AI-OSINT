"""
Pydantic schemas for the FastAPI interface.
"""

from __future__ import annotations

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """
    Request body for text analysis.
    """

    text: str


class RiskResponse(BaseModel):
    score: float
    label: str


class ClassifierResponse(BaseModel):
    confidence: float


class DrugMatchResponse(BaseModel):
    matched_text: str
    canonical_name: str
    confidence: float


class EmojiMatchResponse(BaseModel):
    emoji: str
    canonical_name: str
    confidence: float


class EntityResponse(BaseModel):
    text: str
    label: str


class AnalyzeResponse(BaseModel):
    """
    Response returned after text analysis.
    """

    text: str
    risk: RiskResponse
    classifier: ClassifierResponse
    drug_matches: list[DrugMatchResponse]
    emoji_matches: list[EmojiMatchResponse]
    entities: list[EntityResponse]
