"""Tests for BackfillOrchestrator.validate (T033/T034, FR-008)."""

from __future__ import annotations

from orchestration.operators.backfill_orchestrator import (
    BackfillOrchestrator,
    BackfillRequest,
)


def _req(**over):
    base = {
        "dataset": "worldbank:NY.GDP.MKTP.KD.ZG",
        "start_period": "2023-01-01",
        "end_period": "2023-01-07",
        "reason": "Re-extract after schema change",
        "requested_by": "alice@klibra.local",
        "code_version": "0.1.0",
        "expected_impact": "minor_correction",
    }
    base.update(over)
    return BackfillRequest(**base)


def test_validate_happy_path(monkeypatch) -> None:
    monkeypatch.delenv("KLIBRA_BACKFILL_MAX_RANGE_DAYS", raising=False)
    ok, errs = BackfillOrchestrator.validate(_req())
    assert ok is True
    assert errs == []


def test_validate_empty_field(monkeypatch) -> None:
    ok, errs = BackfillOrchestrator.validate(_req(reason=""))
    assert ok is False
    assert any("reason" in e for e in errs)


def test_validate_inverted_range(monkeypatch) -> None:
    ok, errs = BackfillOrchestrator.validate(
        _req(start_period="2023-02-01", end_period="2023-01-01")
    )
    assert ok is False
    assert any("start_period must be <=" in e for e in errs)


def test_validate_bad_semver(monkeypatch) -> None:
    ok, errs = BackfillOrchestrator.validate(_req(code_version="v1"))
    assert ok is False
    assert any("code_version" in e for e in errs)


def test_validate_max_range_days_exceeded(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_BACKFILL_MAX_RANGE_DAYS", "5")
    ok, errs = BackfillOrchestrator.validate(
        _req(start_period="2023-01-01", end_period="2023-12-31")
    )
    assert ok is False
    assert any("exceeds 5 days" in e for e in errs)


def test_submit_returns_idempotency_key(monkeypatch) -> None:
    monkeypatch.delenv("KLIBRA_BACKFILL_MAX_RANGE_DAYS", raising=False)
    receipt = BackfillOrchestrator().submit(_req())
    assert "idempotency_key" in receipt
    assert receipt["run_id"]
    assert receipt["validation_status"] in {"PENDING", "APPROVED"}
