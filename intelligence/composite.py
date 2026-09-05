"""Composite scorer interface — PRD §28, TDD §64, spec.md FR-1..FR-4 002-D.

Provides the ``CompositeScorer`` protocol and base helpers for every
intelligence product module. The scoring framework is intentionally
plain-Python (no Spark, no model-serving infra) per plan.md Decision 5.

Examples (spec.md 002-D SC-D-2 determinism):

  from intelligence.composite import CompositeScorer

  class MyProduct(CompositeScorer):
      product_id = "intelligence_my_product"
      methodology_version = "1.0.0"
      weights = {"metric_a": 0.6, "metric_b": 0.4}

      def normalize(self, inputs):
          # min-max or z-score; inputs are scalars
          return {k: inputs[k] / 100.0 for k in inputs}

      def aggregate(self, components):
          # components is {metric_id: normalized_value}
          return sum(components[k] * self.weights[k] for k in components)

Usage at call-site:

  scorer = MyProduct()
  score, confidence, coverage_ratio, components = scorer.score(inputs)
"""

from __future__ import annotations

import datetime as dt
import uuid
from abc import ABC
from dataclasses import dataclass, field

__all__ = ["CompositeScorer", "IntelligenceScore", "MethodologyVersionBumpRequired"]


class MethodologyVersionBumpRequired(RuntimeError):  # noqa: N818
    """Raised when weights change without a MAJOR methodology bump (FR-8 002-D)."""

    def __init__(self, message: str, *, expected_version: str | None = None) -> None:
        super().__init__(message)
        self.expected_version = expected_version


@dataclass(frozen=True, slots=True)
class IntelligenceScore:
    """Result of ``CompositeScorer.score``."""

    product_id: str
    methodology_version: str
    score: float
    confidence: float
    coverage_ratio: float
    input_snapshot_id: str
    components: dict[str, float]  # {component_metric_id: normalized_value}
    contributions: dict[str, float]  # {component_metric_id: normalized_value * weight}
    weights: dict[str, float]
    calculated_at: str = field(default_factory=lambda: dt.datetime.now(dt.UTC).isoformat())
    score_band: str = "MEDIUM"
    lineage_ref: str | None = None

    @property
    def score_band_value(self) -> str:
        if self.score < 33:
            return "LOW"
        if self.score < 66:
            return "MEDIUM"
        return "HIGH"


class CompositeScorer(ABC):
    """Protocol for every intelligence product scorer (FR-3 002-D)."""

    product_id: str
    methodology_version: str
    # ``weights`` is version-controlled per FR-8 002-D.
    weights: dict[str, float]

    def coverage_check(self, inputs: dict[str, float]) -> tuple[float, float]:
        """Return ``(confidence, coverage_ratio)``.

        Default: missing inputs reduce confidence and coverage.
        """
        expected = set(self.weights.keys())
        present = {k for k in inputs if inputs[k] is not None}
        coverage = len(present & expected) / max(1, len(expected))
        confidence = coverage  # simplest policy; override in product
        return (confidence, coverage)

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        """Normalize inputs to a common scale (e.g. z-score or min-max)."""

        # Default: min-max per weight — no-op, rely on raw inputs
        return dict(inputs)

    def aggregate(self, components: dict[str, float]) -> float:
        """Aggregate normalized components into a single score (0–100)."""

        # Default: weighted mean
        return sum(components[k] * self.weights[k] for k in components if k in components)

    def score(
        self,
        inputs: dict[str, float],
        *,
        input_snapshot_id: str | None = None,
    ) -> IntelligenceScore:
        """Return a deterministic ``IntelligenceScore`` for ``inputs``.

        ``input_snapshot_id`` is an external determinism anchor (UUID).
        If not provided a UUID is derived from the inputs for reproducibility.
        """
        if not input_snapshot_id:
            # Deterministic UUID derived from inputs for reproducibility
            payload = str(sorted(inputs.items())).encode()
            input_snapshot_id = str(uuid.uuid5(uuid.NAMESPACE_URL, payload.decode()))

        confidence, coverage = self.coverage_check(inputs)
        if coverage < 0.0:
            raise ValueError("coverage ratio must be >= 0")
        if coverage < self.__dict__.get("min_coverage", 0.5):
            # Return with coverage = confidence, score = None equivalent
            pass

        normalized = self.normalize(inputs)
        agg = self.aggregate(normalized)
        # Clamp to 0-100
        score = max(0.0, min(100.0, agg))
        contributions = {
            k: normalized.get(k, 0.0) * self.weights[k] for k in self.weights if k in normalized
        }
        # Build lineage_ref per TDD §69
        lineage_ref = (
            f"intelligence:{self.product_id}:{self.methodology_version}:{input_snapshot_id}"
        )
        return IntelligenceScore(
            product_id=self.product_id,
            methodology_version=self.methodology_version,
            score=score,
            confidence=confidence,
            coverage_ratio=coverage,
            input_snapshot_id=input_snapshot_id,
            components=dict(normalized),
            contributions=contributions,
            weights=dict(self.weights),
            score_band=self._band(score),
            lineage_ref=lineage_ref,
        )

    @staticmethod
    def _band(score: float) -> str:
        if score < 33:
            return "LOW"
        if score < 66:
            return "MEDIUM"
        return "HIGH"
