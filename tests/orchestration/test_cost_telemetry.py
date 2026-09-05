"""Unit tests for T056/T057 — per-dataset cost telemetry (002-F)."""

from __future__ import annotations

from orchestration.util.cost import CostTelemetry, DatasetCost


def test_cost_telemetry_roundtrip() -> None:
    t = CostTelemetry(run_id="r1", api_request_volume=10, compute_hours=1.5)
    d = t.to_dict()
    assert d["run_id"] == "r1"
    assert d["api_request_volume"] == 10
    assert d["compute_hours"] == 1.5


def test_dataset_cost_has_dataset_id() -> None:
    t = DatasetCost(run_id="r1", dataset_id="worldbank.NY.GDP.MKTP.CD")
    assert t.dataset_id == "worldbank.NY.GDP.MKTP.CD"
    d = t.to_dict()
    assert d["dataset_id"] == "worldbank.NY.GDP.MKTP.CD"
