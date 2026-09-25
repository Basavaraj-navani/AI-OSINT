"""
API routes.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from drug_trafficking_osint.application.intelligence.coordinator import (
    IntelligenceCoordinator,
)
from drug_trafficking_osint.interfaces.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ClassifierResponse,
    DrugMatchResponse,
    EmojiMatchResponse,
    EntityResponse,
    RiskResponse,
)

router = APIRouter()


@lru_cache(maxsize=1)
def get_coordinator() -> IntelligenceCoordinator:
    return IntelligenceCoordinator()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a social media post.
    """

    result = get_coordinator().analyze(request.text)

    return AnalyzeResponse(
        text=result.original_text,
        risk=RiskResponse(
            score=result.risk_result.score,
            label=result.risk_result.label,
        ),
        classifier=ClassifierResponse(
            confidence=result.classifier_result.confidence,
        ),
        drug_matches=[
            DrugMatchResponse(
                matched_text=match.matched_text,
                canonical_name=match.canonical_name,
                confidence=match.confidence,
            )
            for match in result.slang_result.matches
        ],
        emoji_matches=[
            EmojiMatchResponse(
                emoji=match.emoji,
                canonical_name=match.canonical_name,
                confidence=match.confidence,
            )
            for match in result.emoji_result.matches
        ],
        entities=[
            EntityResponse(
                text=entity.text,
                label=entity.label,
            )
            for entity in result.ner_result.entities
        ],
    )
