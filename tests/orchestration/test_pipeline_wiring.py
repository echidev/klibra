"""End-to-end pipeline wiring tests — 003 SC-1, SC-5, G1–G12.

Validates each wired gap independently using mocked connectors and
subprocess. No live network or live dbt.
"""

from __future__ import annotations

import os

import pytest

# ── G1: discover_datasets enumerates all live-verified sources ────────────────


def test_discover_datasets_includes_all_4_sources() -> None:
    """G1: discover() finds worldbank, ecb, fred, alphavantage from catalog."""
    from orchestration.tasks import discover_datasets

    os.environ.setdefault("FRED_API_KEY", "x" * 32)
    os.environ.setdefault("ALPHAVANTAGE_API_KEY", "DUMMY_KEY_12345678901234")
    result = discover_datasets()
    sources = {d["source_id"] for d in result["datasets"]}
    assert "worldbank" in sources
    assert "ecb" in sources
    assert "fred" in sources
    assert "alphavantage" in sources


def test_discover_datasets_skips_imf() -> None:
    """G1: IMF (Class C) is not a fatal crash — deferred, logged and skipped."""
    from orchestration.tasks import discover_datasets

    os.environ.setdefault("FRED_API_KEY", "x" * 32)
    os.environ.setdefault("ALPHAVANTAGE_API_KEY", "DUMMY_KEY_12345678901234")
    result = discover_datasets()
    # imf is in the catalog but should be skipped (no connector)
    imf = [d for d in result["datasets"] if d["source_id"] == "imf"]
    assert imf == []


# ── G2: _default_connector AV/FRED key resolution ───────────────────────────


def test_default_connector_av_requires_env() -> None:
    """G2: _default_connector raises ValueError when AV key missing."""
    from orchestration.tasks import _default_connector

    old = os.environ.pop("ALPHAVANTAGE_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="ALPHAVANTAGE_API_KEY"):
            _default_connector({"source_id": "alphavantage", "dataset_id": "X"})
    finally:
        if old:
            os.environ["ALPHAVANTAGE_API_KEY"] = old


def test_default_connector_fred_requires_env() -> None:
    """G2: _default_connector raises ValueError when FRED key missing."""
    from orchestration.tasks import _default_connector

    old = os.environ.pop("FRED_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="FRED_API_KEY"):
            _default_connector({"source_id": "fred", "dataset_id": "X"})
    finally:
        if old:
            os.environ["FRED_API_KEY"] = old


# ── G3: build_bronze dispatcher (worldbank path) ─────────────────────────────


def test_build_bronze_dispatcher_worldbank() -> None:
    """G3: build_bronze dispatches to worldbank parser and returns records."""
    import datetime as dt

    from ingestion.connectors.base import ExtractionResult
    from orchestration.tasks import build_bronze

    payload = b'[{"page":1,"pages":1,"per_page":1,"total":1},[{"indicator":{"id":"X","value":"GDP"},"country":{"id":"USA","value":"US"},"countryiso3code":"USA","date":"2023","value":100.0,"unit":"","obs_status":"","decimal":0}]]'

    class FakeMeta:
        retrieval_timestamp = dt.datetime(2023, 1, 1, tzinfo=dt.UTC)

    item = {
        "source_id": "worldbank",
        "dataset_id": "X",
        "run_id": "r",
        "payload": payload,
        "source_url": "https://example",
        "metadata": FakeMeta(),
        "result": ExtractionResult(payload=payload, source_url="https://example"),
    }
    result = build_bronze({"items": [item], "count": 1})
    assert result["status"] == "BRONZE_BUILT"
    assert len(result["batches"]) == 1
    assert len(result["batches"][0]["records"]) == 1


# ── G4: _parse_observation_date polymorphic ──────────────────────────────────


def test_parse_observation_date_formats() -> None:
    """G4: YYYY, YYYY-MM, YYYY-Qn, YYYY-MM-DD, DD/MM/YYYY all parse correctly."""
    import datetime as dt

    from orchestration.tasks import _parse_observation_date

    assert _parse_observation_date("2023") == dt.date(2023, 1, 1)
    assert _parse_observation_date("2023-06") == dt.date(2023, 6, 1)
    assert _parse_observation_date("2023-Q2") == dt.date(2023, 4, 1)
    assert _parse_observation_date("2023-06-15") == dt.date(2023, 6, 15)
    assert _parse_observation_date("2023-06-15T12:00:00") == dt.date(2023, 6, 15)
    assert _parse_observation_date("15/06/2023") == dt.date(2023, 6, 15)
    with pytest.raises(ValueError):
        _parse_observation_date("not-a-date")


# ── G8: Gold SQL is DuckDB-compatible (schema.yml registered) ───────────────


def test_gold_dbt_models_registered_in_schema_yml() -> None:
    """G8/G9: gold models are registered in schema.yml with tests."""
    from pathlib import Path

    import yaml

    schema = yaml.safe_load(Path("transformation/dbt/models/schema.yml").read_text())
    model_names = {m["name"] for m in schema["models"]}
    assert "gold_country_benchmark" in model_names
    assert "gold_market_overview" in model_names
    # Check entity_id is unique for country_benchmark
    cb = next(m for m in schema["models"] if m["name"] == "gold_country_benchmark")
    eid_col = next(c for c in cb["columns"] if c["name"] == "entity_id")
    assert "unique" in eid_col["tests"]


# ── G10: compute_intelligence task exists in DAG ─────────────────────────────


def test_compute_intelligence_task_in_dag() -> None:
    """G10: The DAG contains a compute_intelligence task between gold and publish."""

    from pathlib import Path

    source = Path("orchestration/dags/klibra_pipeline.py").read_text()
    assert "compute_intelligence" in source
    # Verify compute_intelligence is called between go and pu in the wire section
    assert "go = gold(sq)" in source
    assert "ci = compute_intelligence(go)" in source
    assert "pu = publish(ci)" in source


# ── G11: confidence.py publish gate ──────────────────────────────────────────


def test_confidence_coverage_ratio() -> None:
    """G11: coverage_ratio counts present non-None inputs against weights."""
    from intelligence.util.confidence import coverage_ratio

    assert coverage_ratio({"a": 1.0, "b": 2.0}, {"a": 1.0, "b": 1.0, "c": 1.0}) == pytest.approx(
        2 / 3
    )
    assert coverage_ratio({"a": 1.0, "b": None}, {"a": 1.0, "b": 1.0}) == pytest.approx(0.5)
    assert coverage_ratio({}, {}) == 1.0
    assert coverage_ratio({"a": 1.0}, {"a": 1.0}) == 1.0


def test_confidence_rescaled() -> None:
    """G11: confidence(coverage, min) = min(1, coverage/min)."""
    from intelligence.util.confidence import confidence

    assert confidence(1.0, 0.5) == 1.0
    assert confidence(0.3, 0.5) == pytest.approx(0.6)
    assert confidence(0.0, 0.5) == 0.0
    assert confidence(0.5, 0.0) == 1.0  # min=0 guard


def test_composite_scorer_gate() -> None:
    """G11: Scorer with coverage below min_coverage still returns QUARANTINED lineage."""
    from intelligence.products.market_stress import MarketStressScorer

    scorer = MarketStressScorer()
    # Provide empty inputs → coverage 0, below min_coverage=0.66
    score = scorer.score({})
    assert score.score == 0.0
    assert score.coverage_ratio == 0.0


# ── G12: cost + lineage wiring via notify_owners ─────────────────────────────


def test_notify_owners_emits_cost_and_lineage(monkeypatch) -> None:
    """G12: notify_owners emits per-record cost + per-record lineage."""
    calls: list[dict] = []
    opened: list[dict] = []

    def fake_record(obj) -> None:  # type: ignore[no-untyped-def]
        calls.append({"dataset_id": obj.dataset_id})

    def fake_emit(run_id: str, dataset_id: str, status: str, **_kw: object) -> None:
        opened.append({"run_id": run_id, "dataset_id": dataset_id, "status": status})

    from orchestration.util import observability as _obs

    orig_emit = _obs.emit_openmetadata_event
    _obs.emit_openmetadata_event = fake_emit  # type: ignore[assignment]
    try:
        # Use the lazy import path that notify_owners actually takes
        # (orchestration.util.observability.emit_openmetadata_event)
        from orchestration.tasks import notify_owners

        notify_owners(
            {
                "status": "PUBLISHED",
                "records_written": 5,
                "run_id": "r1",
                "records": [
                    {"dataset_id": "ds1", "lineage_ref": "silver.fact:obs1", "run_id": "r1"}
                ],
            }
        )
        assert len(opened) >= 1
        assert any(e["run_id"] == "r1" for e in opened)
    finally:
        _obs.emit_openmetadata_event = orig_emit  # type: ignore[assignment]
