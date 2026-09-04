"""Four-level quality framework — TDD §21, PRD §13.

Quality levels per TDD §21:
- Batch: file exists, payload readable, expected response, record count,
  hash, schema.
- Record: type, nullability, range, allowed values, FK integrity.
- Dataset: duplicate rate, completeness, freshness, temporal continuity,
  cross-field consistency.
- Business: domain-specific rules, reconciliation, expected relationships.

The :class:`QualityFramework` is a single entry point that exposes one
method per level plus a severity classification (TDD §22).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "QualityLevel",
    "QualityOutcome",
    "QualityFramework",
]


class QualityLevel(str, Enum):
    BATCH = "batch"
    RECORD = "record"
    DATASET = "dataset"
    BUSINESS = "business"


class QualityOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    ACCEPTED_WARNING = "ACCEPTED_WARNING"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class QualityFramework:
    """Quality gate with batch/record/dataset/business level checks."""

    def evaluate_batch(
        self, *, payload_present: bool, schema_valid: bool
    ) -> QualityOutcome:
        if not payload_present:
            return QualityOutcome.REJECTED
        if not schema_valid:
            return QualityOutcome.QUARANTINED
        return QualityOutcome.ACCEPTED

    def evaluate_record(
        self, *, value: Any, type_valid: bool, range_valid: bool
    ) -> QualityOutcome:
        if not type_valid:
            return QualityOutcome.QUARANTINED
        if not range_valid:
            return QualityOutcome.ACCEPTED_WARNING
        return QualityOutcome.ACCEPTED

    def evaluate_dataset(
        self, *, duplicate_rate: float, completeness: float
    ) -> QualityOutcome:
        if duplicate_rate > 0.0:
            return QualityOutcome.QUARANTINED
        if completeness < 0.95:
            return QualityOutcome.ACCEPTED_WARNING
        return QualityOutcome.ACCEPTED

    def evaluate_business(self, *, reconciliation_diff: float) -> QualityOutcome:
        if abs(reconciliation_diff) > 0.01:
            return QualityOutcome.QUARANTINED
        return QualityOutcome.ACCEPTED
