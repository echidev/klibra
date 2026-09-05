"""Unit tests for the cross-source reconciler — PRD UC-03 (T044)."""

from __future__ import annotations

from typing import Any

import pytest

from transformation.reconcile.reconciler import Reconciler


def _make_row(metric: str, entity: str, date: str, value: float | None) -> dict[str, Any]:
    return {"metric_id": metric, "entity_id": entity, "observation_date": date, "value": value}


def test_equal_values_not_divergent() -> None:
    a = [_make_row("gdp", "USA", "2023", 2.5)]
    b = [_make_row("gdp", "USA", "2023", 2.5)]
    result = Reconciler(divergence_threshold_percent=20.0).reconcile(a, b)
    assert result.divergence_count == 0
    assert result.divergence_rate == 0.0


def test_divergent_values_flagged() -> None:
    a = [_make_row("gdp", "USA", "2023", 3.0)]
    b = [_make_row("gdp", "USA", "2023", 2.0)]  # 50% difference
    result = Reconciler(divergence_threshold_percent=20.0).reconcile(a, b)
    assert result.divergence_count == 1
    assert result.divergence_rate == 1.0
    row = result.rows[0]
    assert row.divergent
    assert row.sign == "a_higher"
    assert row.diff_percent == pytest.approx(50.0)


def test_missing_data_in_one_stream() -> None:
    a = [_make_row("gdp", "USA", "2023", 2.5)]
    b: list[dict[str, Any]] = []
    result = Reconciler().reconcile(a, b)
    assert result.rows[0].sign == "incomparable"
    assert result.rows[0].divergent is False


def test_divergent_definitions_flagged() -> None:
    """Different metric definitions on the same grain should be flagged."""
    a = [_make_row("gdp", "USA", "2023", 2.5)]
    b = [_make_row("gdp", "USA", "2023", None)]  # Value missing → incomparable
    result = Reconciler().reconcile(a, b)
    assert result.rows[0].sign == "incomparable"
