"""Tests for build_gold/publish_gold return-shape contract (T021/T022, FR-004/FR-011)."""

from __future__ import annotations

import pytest

from orchestration.tasks import build_gold, publish_gold


def _silver_passed() -> dict:
    return {
        "records": [
            {
                "observation_id": "run-1:US:GDP:2023-01-01",
                "effective_from": "2023-01-01",
                "effective_to": None,
                "quality_status": "ACCEPTED",
                "value": 2.5,
                "metric_id": "gdp_growth_rate",
                "run_id": "run-1",
            }
        ]
    }


def test_legacy_fast_path_shape() -> None:
    out = build_gold(_silver_passed())
    assert {"status", "records", "products", "row_counts", "run_id"} == set(out.keys())
    assert out["status"] == "GOLD_BUILT"
    assert len(out["records"]) == 1
    assert out["run_id"] == "run-1"


@pytest.mark.parametrize("shape", ["legacy", "dbt"])
@pytest.mark.parametrize("payload", ["records", "row_counts"])
def test_publish_gold_accepts_records_or_rowcounts(shape: str, payload: str) -> None:
    if payload == "records":
        batch = build_gold(_silver_passed())
    else:
        batch = {
            "status": "GOLD_BUILT",
            "records": [],
            "products": {"gold_macro_indicators": 0},
            "row_counts": {
                "gold_macro_indicators": 5,
                "gold_country_benchmark": 3,
                "gold_market_overview": 2,
            },
            "run_id": "r",
        }
    if shape == "legacy" and payload == "records":
        out = publish_gold(batch)
        assert out["status"] == "PUBLISHED"
    else:
        out = publish_gold(batch)
        assert out["status"] == "PUBLISHED"


def test_publish_gold_empty_raises() -> None:
    with pytest.raises(ValueError, match="cannot publish an empty Gold batch"):
        publish_gold(
            {"records": [], "row_counts": {}, "status": "GOLD_BUILT", "products": {}, "run_id": ""}
        )
