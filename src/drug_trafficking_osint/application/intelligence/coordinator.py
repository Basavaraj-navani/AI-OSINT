"""
Coordinates all intelligence detectors.
"""

from __future__ import annotations

from datetime import datetime

from drug_trafficking_osint.application.intelligence.models import (
    IntelligenceResult,
)
from drug_trafficking_osint.infrastructure.classifier.classifier import (
    AIClassifier,
)
from drug_trafficking_osint.infrastructure.database.database import (
    DatabaseManager,
)
from drug_trafficking_osint.infrastructure.database.models import (
    AnalysisRecord,
)
from drug_trafficking_osint.infrastructure.emoji_engine.emoji_detector import (
    EmojiDetector,
)
from drug_trafficking_osint.infrastructure.graph.graph_builder import (
    GraphBuilder,
)
from drug_trafficking_osint.infrastructure.graph.models import (
    GraphEdge,
    GraphNode,
)
from drug_trafficking_osint.infrastructure.ner_engine.ner_detector import (
    NERDetector,
)
from drug_trafficking_osint.infrastructure.nlp.pipeline import (
    PreprocessingPipeline,
)
from drug_trafficking_osint.infrastructure.risk_engine.risk_calculator import (
    RiskCalculator,
)
from drug_trafficking_osint.infrastructure.slang_engine.slang_detector import (
    SlangDetector,
)


class IntelligenceCoordinator:
    """
    Runs all intelligence modules on input text.
    """

    def __init__(self) -> None:
        self.pipeline = PreprocessingPipeline()
        self.slang_detector = SlangDetector()
        self.emoji_detector = EmojiDetector()
        self.ner_detector = NERDetector()
        self.classifier = AIClassifier()
        self.risk_calculator = RiskCalculator()
        self.database = DatabaseManager()
        self.graph_builder = GraphBuilder()

    def analyze(self, text: str) -> IntelligenceResult:
        """
        Analyze text using all available intelligence detectors.
        """

        processed = self.pipeline.process(text)

        slang_result = self.slang_detector.detect(processed)
        emoji_result = self.emoji_detector.detect(text)
        ner_result = self.ner_detector.detect(text)
        classifier_result = self.classifier.predict(text)

        slang_score = min(len(slang_result.matches) * 0.25, 1.0)
        emoji_score = min(len(emoji_result.matches) * 0.20, 1.0)
        ner_score = min(len(ner_result.entities) * 0.20, 1.0)

        risk_result = self.risk_calculator.calculate(
            classifier_score=classifier_result.confidence,
            slang_score=slang_score,
            emoji_score=emoji_score,
            ner_score=ner_score,
        )

        record = AnalysisRecord(
            text=text,
            risk_score=risk_result.score,
            risk_label=risk_result.label,
            created_at=datetime.now(),
        )

        self.database.insert_record(record)

        # -------------------------
        # Build Intelligence Graph
        # -------------------------

        graph = GraphBuilder()

        for entity in ner_result.entities:
            graph.add_node(
                GraphNode(
                    id=entity.text,
                    label=entity.text,
                    type=entity.label,
                )
            )

        entities = list(ner_result.entities)

        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                graph.add_edge(
                    GraphEdge(
                        source=entities[i].text,
                        target=entities[i + 1].text,
                        relationship="CO_OCCURS_WITH",
                    )
                )

        # Optional:
        # print(graph.export_json())

        return IntelligenceResult(
            original_text=text,
            slang_result=slang_result,
            emoji_result=emoji_result,
            ner_result=ner_result,
            classifier_result=classifier_result,
            risk_result=risk_result,
        )
