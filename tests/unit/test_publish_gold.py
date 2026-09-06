"""Tests for publish_gold — see T022."""

from __future__ import annotations

from orchestration.tasks import publish_gold


def test_publish_gold_counts_records() -> None:
    out = publish_gold(
        {
            "status": "GOLD_BUILT",
            "records": [{"a": 1}, {"a": 2}],
            "products": {"gold_macro_indicators": 0},
            "row_counts": {"gold_macro_indicators": 0},
            "run_id": "r1",
        }
    )
    assert out["records_written"] == 2


def test_publish_gold_falls_back_to_row_counts_sum() -> None:
    out = publish_gold(
        {
            "status": "GOLD_BUILT",
            "records": [],
            "products": {
                "gold_macro_indicators": 4,
                "gold_country_benchmark": 6,
                "gold_market_overview": 10,
            },
            "row_counts": {
                "gold_macro_indicators": 4,
                "gold_country_benchmark": 6,
                "gold_market_overview": 10,
            },
            "run_id": "r2",
        }
    )
    assert out["records_written"] == 20
