"""Pipeline-plane metrics — TDD §67.1, plan.md."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["PipelineRunMetrics"]


@dataclass(frozen=True, slots=True)
class PipelineRunMetrics:
    """Pipeline-level observability signals (TDD §67.1)."""

    run_id: str
    pipeline_id: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    retries: int = 0
    failure_rate: float = 0.0
    api_latency_ms: float | None = None
    api_response_code: int | None = None
    records_received: int | None = None
    records_written: int | None = None
    compute_usage_seconds: float | None = None

    @property
    def duration(self) -> float | None:
        """Return wall-clock duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return self.duration_seconds
