"""Pipeline-plane metrics — TDD §67.1, plan.md, Spec 004 remediation.

Module-level counters per plan §Monitoring for observability:
- ``storage_writes_total``
- ``quarantine_records_total``
- ``gold_row_counts_correctness_total``
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime

__all__ = [
    "PipelineRunMetrics",
    "Counter",
    "storage_writes_total",
    "quarantine_records_total",
    "gold_row_counts_correctness_total",
]


class Counter:
    """Minimal thread-safe counter for pipeline metrics (no external deps)."""

    def __init__(self) -> None:
        self._value: int = 0
        self._lock = threading.Lock()

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: int = 1) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0

    def __repr__(self) -> str:
        return f"Counter({self.value})"


# ── Module-level counters (plan §Monitoring) ─────────────────────────────
storage_writes_total = Counter()
quarantine_records_total = Counter()
gold_row_counts_correctness_total = Counter()


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
