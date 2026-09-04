"""Data-plane metrics — TDD §67.2, plan.md."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DataQualityMetrics"]


@dataclass(frozen=True, slots=True)
class DataQualityMetrics:
    """Data-level observability signals (TDD §67.2)."""

    freshness_lag_hours: float | None = None
    row_count: int | None = None
    null_rate: float | None = None
    duplicate_rate: float | None = None
    distribution_drift: float | None = None
    missing_periods: int | None = None
    schema_drift_detected: bool = False
    quality_score: float | None = None
    coverage_ratio: float | None = None

    @property
    def null_ratio(self) -> float | None:
        return self.null_rate

    @property
    def is_fresh(self) -> bool | None:
        if self.freshness_lag_hours is None:
            return None
        return self.freshness_lag_hours < 24
