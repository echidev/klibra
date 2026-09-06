"""Backfill orchestrator — TDD §17, FR-F-2 (002-F).

Validates and tracks backfill runs. Dual-run idempotency is enforced
via the same idempotency key used by ingestion (PRD FR-F-2 + TDD §71).

Required fields per TDD §17:
  dataset, start_period, end_period, reason, requested_by,
  code_version, expected_impact, validation_status.
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = ["BackfillRequest", "BackfillOrchestrator", "BackfillStatus", "BackfillValidationError"]


class BackfillStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BackfillValidationError(ValueError):
    """Raised when a BackfillRequest is missing required fields or has invalid time range."""


@dataclass(frozen=True, slots=True)
class BackfillRequest:
    dataset: str
    start_period: str
    end_period: str
    reason: str
    requested_by: str
    code_version: str
    expected_impact: str
    validation_status: BackfillStatus = BackfillStatus.PENDING
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: dt.datetime.now(dt.UTC).isoformat())


def _validate(req: BackfillRequest) -> list[str]:
    errors: list[str] = []
    required = {
        "dataset": req.dataset,
        "start_period": req.start_period,
        "end_period": req.end_period,
        "reason": req.reason,
        "requested_by": req.requested_by,
        "code_version": req.code_version,
        "expected_impact": req.expected_impact,
    }
    for name, val in required.items():
        if not isinstance(val, str) or not val.strip():
            errors.append(f"required field missing or empty: {name!r}")
    if req.start_period > req.end_period:
        errors.append("start_period must be <= end_period")
    parts = req.code_version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        errors.append("code_version must be semver (X.Y.Z)")
    return errors


class BackfillOrchestrator:
    """Validate, track, and dispatch backfill runs.

    In production this would dispatch to the Airflow backfill DAG; in
    local dev it returns the validated request and an idempotency key.
    """

    def __init__(self) -> None:
        self._history: list[BackfillRequest] = []

    @classmethod
    def validate(cls, req: BackfillRequest) -> tuple[bool, list[str]]:
        """Return ``(is_valid, errors)`` for a backfill request (FR-008).

        Extends :func:`_validate` with max-range enforcement defaulting to
        365 days, overridable via ``KLIBRA_BACKFILL_MAX_RANGE_DAYS``.
        """
        errors = _validate(req)
        if errors:
            return (False, errors)
        try:
            start = dt.date.fromisoformat(req.start_period)
            end = dt.date.fromisoformat(req.end_period)
        except ValueError:
            return (False, ["start_period/end_period must be ISO dates (YYYY-MM-DD)"])
        max_days_str = os.environ.get("KLIBRA_BACKFILL_MAX_RANGE_DAYS", "365")
        try:
            max_days = int(max_days_str)
        except ValueError:
            max_days = 365
        if (end - start).days > max_days:
            return (False, [f"date range exceeds {max_days} days (KLIBRA_BACKFILL_MAX_RANGE_DAYS)"])
        return (True, [])

    def submit(self, req: BackfillRequest) -> dict[str, Any]:
        """Validate and queue a backfill. Returns an idempotency key + the request."""

        errors = _validate(req)
        if errors:
            raise BackfillValidationError("; ".join(errors))
        self._history.append(req)
        from ingestion.util.idempotency import compute_idempotency_key

        idem_key = compute_idempotency_key(
            req.dataset,
            req.dataset,
            req.start_period + "_" + req.end_period,
            req.code_version,
            req.expected_impact,
        )
        return {
            "run_id": req.run_id,
            "idempotency_key": idem_key,
            "validation_status": req.validation_status.value,
            "request": req,
        }

    def history(self) -> list[BackfillRequest]:
        return list(self._history)
