"""Unit tests for T054 — BackfillOrchestrator (002-F)."""

from __future__ import annotations

import pytest

from orchestration.operators.backfill_orchestrator import (
    BackfillOrchestrator,
    BackfillRequest,
    BackfillValidationError,
)


def _valid_request() -> BackfillRequest:
    return BackfillRequest(
        dataset="worldbank.NY.GDP.MKTP.CD",
        start_period="2020-01-01",
        end_period="2020-03-31",
        reason="reprocess after Silver fix",
        requested_by="eng@klibra.local",
        code_version="1.0.0",
        expected_impact="100 rows",
    )


def test_backfill_valid() -> None:
    req = _valid_request()
    orchestrator = BackfillOrchestrator()
    result = orchestrator.submit(req)
    assert result["run_id"] == req.run_id
    assert "idempotency_key" in result


def test_backfill_missing_reason_rejected() -> None:
    req = BackfillRequest(
        dataset="d",
        start_period="2020-01-01",
        end_period="2020-03-31",
        reason="",
        requested_by="eng@klibra.local",
        code_version="1.0.0",
        expected_impact="100 rows",
    )
    with pytest.raises(BackfillValidationError, match="reason"):
        BackfillOrchestrator().submit(req)


def test_backfill_inverted_range_rejected() -> None:
    req = BackfillRequest(
        dataset="d",
        start_period="2020-04-01",
        end_period="2020-01-01",
        reason="fix",
        requested_by="eng@klibra.local",
        code_version="1.0.0",
        expected_impact="100 rows",
    )
    with pytest.raises(BackfillValidationError, match="start_period must be"):
        BackfillOrchestrator().submit(req)


def test_backfill_history_tracks() -> None:
    orchestrator = BackfillOrchestrator()
    req = _valid_request()
    orchestrator.submit(req)
    assert len(orchestrator.history()) == 1
