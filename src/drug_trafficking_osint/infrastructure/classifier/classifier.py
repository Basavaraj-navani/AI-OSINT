"""
AI classifier using a Hugging Face transformer model.
"""

from __future__ import annotations

from typing import Any

from transformers import pipeline

from drug_trafficking_osint.infrastructure.classifier.constants import (
    CONFIDENCE_THRESHOLD,
    LABEL_HIGH_RISK,
    LABEL_LOW_RISK,
    MODEL_NAME,
    MODEL_REVISION,
)
from drug_trafficking_osint.infrastructure.classifier.exceptions import (
    ModelLoadError,
    PredictionError,
)
from drug_trafficking_osint.infrastructure.classifier.models import (
    ClassificationResult,
)


class AIClassifier:
    """
    AI classifier that predicts the risk level of a text.
    """

    def __init__(self) -> None:
        try:
            self.pipeline = pipeline(
                task="text-classification",
                model=MODEL_NAME,
                revision=MODEL_REVISION,
            )
        except Exception as exc:
            raise ModelLoadError(f"Unable to load transformer model '{MODEL_NAME}'.") from exc

    def predict(self, text: str) -> ClassificationResult:
        """
        Predict the risk level of the given text.
        """
        try:
            prediction: dict[str, Any] = self.pipeline(text)[0]

            confidence = float(prediction.get("score", 0.0))

            label = LABEL_HIGH_RISK if confidence >= CONFIDENCE_THRESHOLD else LABEL_LOW_RISK

            return ClassificationResult(
                label=label,
                confidence=confidence,
            )

        except Exception as exc:
            raise PredictionError("Prediction failed.") from exc
