"""Tests for the gold_country_benchmark dbt model (T046)."""

from __future__ import annotations

import pathlib

GOLD_PATH = pathlib.Path("transformation/gold/models/gold_country_benchmark.sql")


def test_gold_country_benchmark_model_exists() -> None:
    assert GOLD_PATH.exists(), f"missing {GOLD_PATH}"


def test_gold_country_benchmark_pivots_market_stress_basket() -> None:
    text = GOLD_PATH.read_text()
    for metric in ("gdp_growth_rate", "inflation_rate", "unemployment_rate", "debt_to_gdp"):
        assert metric in text, f"gold_country_benchmark missing {metric}"


def test_gold_country_benchmark_filters_latest_only() -> None:
    text = GOLD_PATH.read_text()
    assert "effective_to is null" in text
    assert "row_number() over" in text
    assert "order by effective_from desc" in text
