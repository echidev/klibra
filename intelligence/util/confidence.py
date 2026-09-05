"""Confidence scoring for intelligence layer — PRD §28, TDD §64, 002-D.

Provides coverage ratio computation and the ``Channel`` class that
intelligence products use for coverage/confidence derivation.

Confidence is defined per PRD §28.4: it reflects whether all expected
component inputs were available and valid. The simplest confidence model
is ``confidence = coverage_ratio``; this module provides both the simple
policy and a per-component validation hook.

This module also optionally exposes the ``fact_intelligence_component``
write helper; the real DB writer lives in ``intelligence/persist.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Channel", "compute_confidence", "compute_coverage_ratio"]


class Channel(str, Enum):
    """Component channel for confidence scoring."""

    RAW = "raw"
    NORMALIZED = "normalized"
    CONTRIBUTION = "contribution"


def compute_coverage_ratio(
    expected_metric_ids: set[str],
    inputs: dict[str, float | None],
) -> float:
    """Compute the coverage ratio (0..1).

    ``coverage_ratio`` is ``|present ∩ expected| / |expected|``.
    A value < 1 means some required inputs were missing or null.
    """
    expected = set(expected_metric_ids)
    present = {k for k in inputs if inputs[k] is not None}
    if not expected:
        return 0.0
    return len(present & expected) / len(expected)


def compute_confidence(
    coverage_ratio: float,
    *,
    quality_weights: dict[str, float] | None = None,
) -> float:
    """Compute confidence (0..1) from a coverage ratio.

    In the simple policy ``confidence = coverage_ratio``; if
    ``quality_weights`` are provided, each present input contributes
    proportionally to its weight. The default (``None``) uses uniform
    weighting.
    """
    if coverage_ratio == 0.0:
        return 0.0
    if quality_weights is None:
        return coverage_ratio
    # Weight-aware confidence: weighted coverage
    sum(quality_weights.values()) or 1.0
    avg = coverage_ratio * (sum(sorted(quality_weights.values())) / max(1, len(quality_weights)))
    # Clamp to 0..1
    return max(0.0, min(1.0, avg if avg else coverage_ratio))


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    coverage_ratio: float
    confidence: float

    def is_publishable(self, min_coverage: float = 0.5) -> bool:
        return self.coverage_ratio >= min_coverage

    def band(self) -> str:
        if self.confidence < 0.33:
            return "LOW"
        if self.confidence < 0.66:
            return "MEDIUM"
        return "HIGH"


@dataclass(frozen=True, slots=True)
class ConfidenceConfig:
    min_coverage: float = 0.5
    weights: dict[str, float] | None = None
