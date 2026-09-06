"""Unit tests for _parse_gold_row_counts (T016, FR-003)."""

from __future__ import annotations

from orchestration.tasks import _parse_gold_row_counts


def test_parse_row_counts_three_products() -> None:
    rr = {
        "results": [
            {"unique_id": "model.klibra.gold_macro_indicators", "different_result": [1, 2, 3]},
            {"unique_id": "model.klibra.gold_country_benchmark", "different_result": [1, 2]},
            {"unique_id": "model.klibra.gold_market_overview", "different_result": []},
            {
                "unique_id": "model.klibra.gold_interest_rate_monitor",
                "different_result": [9],
            },  # not in target set in helper but in set
        ]
    }
    out = _parse_gold_row_counts(rr)
    assert out["gold_macro_indicators"] == 3
    assert out["gold_country_benchmark"] == 2
    assert out["gold_market_overview"] == 0


def test_parse_row_counts_dict_rows_inserted() -> None:
    rr = {
        "results": [
            {
                "unique_id": "model.klibra.gold_macro_indicators",
                "different_result": {"rows_inserted": 7},
            }
        ]
    }
    assert _parse_gold_row_counts(rr)["gold_macro_indicators"] == 7


def test_parse_row_counts_missing_is_zero() -> None:
    assert _parse_gold_row_counts({"results": []}) == {}


def test_parse_row_counts_ignores_non_model_ids() -> None:
    rr = {
        "results": [{"unique_id": "seed.klibra.gold_macro_indicators", "different_result": [1, 2]}]
    }
    assert _parse_gold_row_counts(rr) == {}
