"""
Constants used by the AI classifier.
"""

from __future__ import annotations

MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
MODEL_REVISION = "714eb0fa89d2f80546fda750413ed43d93601a13"

LABEL_HIGH_RISK = "HIGH_RISK"
LABEL_LOW_RISK = "LOW_RISK"

CONFIDENCE_THRESHOLD = 0.75
