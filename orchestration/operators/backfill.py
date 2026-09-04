"""Backfill operator — TDD §17.

Validates a backfill request and emits the standardized audit record.
TDD §17 requires:
- dataset, start_period, end_period, reason, requested_by,
  code_version, expected_impact, validation_status.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum

__all__ = ["BackfillRequest", "ValidationStatus", "validate_backfill"]


class ValidationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class BackfillRequest:
    dataset: str
    start_period: str
    end_period: str
    reason: str
    requested_by: str
    code_version: str
    expected_impact: str
    validation_status: ValidationStatus = ValidationStatus.PENDING


def validate_backfill(req: BackfillRequest) -> tuple[bool, list[str]]:
    """Return ``(ok, error_messages)`` for a backfill request.

    A backfill is valid if all of the following hold:
    - ``start_period <= end_period``
    - ``reason`` and ``requested_by`` are non‑empty
    - ``code_version`` follows semver
    """
    errors: list[str] = []
    if not req.reason:
        errors.append("reason is required")
    if not req.requested_by:
        errors.append("requested_by is required")
    if req.start_period > req.end_period:
        errors.append("start_period must be <= end_period")
    parts = req.code_version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        errors.append("code_version must be semver (X.Y.Z)")
    return (len(errors) == 0, errors)
