"""Cost telemetry hooks — PRD §34, TDD §44.

Emits the cost and consumption signals required for cost governance:

- API request volume
- Compute hours
- Storage growth
- Query bytes scanned
- Retry amplification
- Pipeline runtime

In production these feed into AWS Cost Explorer + CloudWatch metrics; in
local dev we record via the structured logger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ingestion.util.logging import log_event

__all__ = ["CostTelemetry", "DatasetCost", "record_cost_signal", "record_dataset_cost"]


@dataclass(slots=True)
class CostTelemetry:
    """Cost and consumption observability signals for a pipeline run."""

    run_id: str
    api_request_volume: int = 0
    compute_hours: float = 0.0
    storage_growth_bytes: int = 0
    query_bytes_scanned: int = 0
    retry_count: int = 0
    runtime_seconds: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "api_request_volume": self.api_request_volume,
            "compute_hours": self.compute_hours,
            "storage_growth_bytes": self.storage_growth_bytes,
            "query_bytes_scanned": self.query_bytes_scanned,
            "retry_count": self.retry_count,
            "runtime_seconds": self.runtime_seconds,
            **self.extra,
        }


def record_cost_signal(t: CostTelemetry) -> None:
    """Record a cost telemetry sample (PRD §34)."""
    log_event(
        level=20,  # logging.INFO
        message=f"cost signal for run {t.run_id}",
        service="klibra-cost",
        details=t.to_dict(),
    )


@dataclass(slots=True)
class DatasetCost(CostTelemetry):
    """Per-dataset cost extension (002-F T056) that routes via OpenMetadata.

    Extends ``CostTelemetry`` with ``dataset_id`` for per-dataset
    observability on the same OpenMetadata + CloudWatch emit path.
    """

    dataset_id: str = ""  # additional required field for per-dataset granularity

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["dataset_id"] = self.dataset_id
        return base


def record_dataset_cost(t: DatasetCost) -> None:
    """Record a per-dataset cost sample (FR-F-4, T056)."""
    log_event(
        level=20,  # logging.INFO
        message=f"per-dataset cost for {t.dataset_id} run {t.run_id}",
        service="klibra-cost-per-dataset",
        dataset_id=t.dataset_id,  # type: ignore[arg-type]
        details=t.to_dict(),
    )
