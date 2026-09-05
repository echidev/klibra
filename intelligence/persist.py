"""Intelligence persist helpers — TDD §65, FR-2 002-D.

Writes ``fact_intelligence_score`` + ``fact_intelligence_component`` rows
matching the schema in ``V002__add_metric_and_intelligence_tables.sql``.

Implements a lightweight in-memory store (for tests/local) and a Dict
interface so that production can route to PostgreSQL later without
changing the intelligence product modules.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from intelligence.composite import IntelligenceScore

__all__ = ["IntelligenceStore", "persist_score"]


@dataclass(slots=True)
class IntelligenceStore:
    """In-memory store for intelligence score + component tables.

    Production: swap ``engine`` for a real ``psycopg2``/``SQLAlchemy``
    connection; the methods stay identical.
    """

    scores: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)

    def save(
        self,
        score: IntelligenceScore,
        *,
        entity_id: str,
        observation_period: str,
        quality_status: str = "ACCEPTED",
    ) -> dict[str, Any]:
        score_id = str(uuid.uuid4())
        score_row = {
            "score_id": score_id,
            "metric_id": score.product_id,
            "entity_id": entity_id,
            "observation_period": observation_period,
            "score": round(score.score, 4),
            "score_band": score.score_band,
            "confidence": round(score.confidence, 4),
            "coverage_ratio": round(score.coverage_ratio, 4),
            "methodology_version": score.methodology_version,
            "input_snapshot_id": score.input_snapshot_id,
            "calculated_at": score.calculated_at,
            "quality_status": quality_status,
        }
        self.scores.append(score_row)
        for component_metric_id, contribution in score.contributions.items():
            component_row = {
                "score_id": score_id,
                "component_metric_id": component_metric_id,
                "component_value": score.components.get(component_metric_id, 0.0),
                "normalized_value": score.components.get(component_metric_id, 0.0),
                "weight": score.weights.get(component_metric_id, 0.0),
                "contribution": contribution,
                "quality_status": "ACCEPTED",
            }
            self.components.append(component_row)
        return score_row


_default_store = IntelligenceStore()


def persist_score(
    score: IntelligenceScore,
    *,
    entity_id: str,
    observation_period: str,
    store: IntelligenceStore | None = None,
    quality_status: str = "ACCEPTED",
) -> dict[str, Any]:
    """Persist an intelligence score (+ components) to a store."""
    store = store or _default_store
    return store.save(
        score,
        entity_id=entity_id,
        observation_period=observation_period,
        quality_status=quality_status,
    )
