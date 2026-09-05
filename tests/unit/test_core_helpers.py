"""Coverage tests for semantic catalog, orchestration tasks, backfill, cost, intelligence, and remaining gaps."""

from __future__ import annotations

import datetime as dt

import pytest

from intelligence.composite import (
    CompositeScorer,
    IntelligenceScore,
    MethodologyVersionBumpRequired,
)
from intelligence.persist import IntelligenceStore, persist_score
from orchestration.alerts.router import SEVERITY_MAP, AlertRecord, route_alert
from orchestration.metrics.data import DataQualityMetrics
from orchestration.metrics.pipeline import PipelineRunMetrics
from orchestration.operators.backfill import (
    BackfillRequest,
    validate_backfill,
)
from orchestration.operators.backfill_orchestrator import (
    BackfillOrchestrator,
    BackfillValidationError,
)
from orchestration.operators.backfill_orchestrator import (
    BackfillRequest as OrchestratorBackfillRequest,
)
from orchestration.tasks import (
    _canonical_silver,
    build_gold,
    publish_gold,
    run_silver_tests,
    validate_raw,
)
from orchestration.util.cost import (
    CostTelemetry,
    DatasetCost,
    record_cost_signal,
    record_dataset_cost,
)
from orchestration.util.observability import emit_cloudwatch_alarm, emit_openmetadata_event
from orchestration.util.run_state import write_run_state
from semantic.catalog import (
    CANONICAL_METRICS,
    MetricCatalog,
    MetricDefinition,
    MetricRegistry,
    MetricStatus,
    _is_major_bump,
    _is_minor_bump,
    _parse_semver,
)
from semantic.catalog import (
    GovernanceApprovalRequired as GovApproval,
)

# GovernanceApprovalRequired lives in semantic.metrictrax
from semantic.metrictrax import GovernanceApprovalRequired, validate_semver_transition
from semantic.point_in_time import as_of_predicate, filter_as_of

# ── Semantic catalog ──────────────────────────────────────────


def test_parse_semver_valid_and_invalid() -> None:
    assert _parse_semver("1.0.0") == (1, 0, 0)
    assert _parse_semver("2.1.3") == (2, 1, 3)
    with pytest.raises(ValueError):
        _parse_semver("1.0")
    with pytest.raises(ValueError):
        _parse_semver("foo")


def test_is_major_bump() -> None:
    assert _is_major_bump("1.0.0", "2.0.0") is True
    assert _is_major_bump("1.0.0", "1.1.0") is False


def test_is_minor_bump() -> None:
    assert _is_minor_bump("1.0.0", "1.1.0") is True
    assert _is_minor_bump("1.0.0", "2.0.0") is False


def test_metric_definition_bump_semver() -> None:
    md = MetricDefinition(
        metric_id="gdp",
        version="1.0.0",
        name="GDP",
        description="test",
        owner_email="eng@test.com",
        grain=["country"],
        unit="percent",
        formula="x / y",
        source_policy=["worldbank"],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )
    bumped = md.bump_semver("2.0.0", governance_approved=True)
    assert bumped.version == "2.0.0"
    assert bumped.deprecation_status == MetricStatus.ACTIVE
    # major bump without governance approval
    with pytest.raises(GovApproval):
        md.bump_semver("2.0.0")
    # minor bump is fine
    minor = md.bump_semver("1.1.0")
    assert minor.version == "1.1.0"


def test_metric_definition_deprecated_copy() -> None:
    md = MetricDefinition(
        metric_id="gdp",
        version="1.0.0",
        name="GDP",
        description="test",
        owner_email="eng@test.com",
        grain=[],
        unit="percent",
        formula="x",
        source_policy=[],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )
    dep = md.deprecated_copy()
    assert dep.deprecation_status == MetricStatus.DEPRECATED


def test_metric_registry_register_and_active() -> None:
    reg = MetricRegistry()
    md = MetricDefinition(
        metric_id="gdp",
        version="1.0.0",
        name="GDP",
        description="test",
        owner_email="eng@test.com",
        grain=[],
        unit="percent",
        formula="x",
        source_policy=[],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )
    reg.register(md)
    assert reg.active_metric("gdp") is md
    assert reg.list_all() == [md]


def test_metric_registry_active_deprecated() -> None:
    reg = MetricRegistry()
    md = MetricDefinition(
        metric_id="gdp",
        version="1.0.0",
        name="GDP",
        description="test",
        owner_email="eng@test.com",
        grain=[],
        unit="percent",
        formula="x",
        source_policy=[],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )
    reg.register(md)
    dep = reg.deprecated_copy("gdp", "1.0.0")
    assert dep is not None
    assert reg.active_metric("gdp") is None


def test_metric_registry_enumerate_active() -> None:
    reg = MetricRegistry()
    md1 = MetricDefinition(
        metric_id="a",
        version="1.0.0",
        name="A",
        description="test",
        owner_email="eng@test.com",
        grain=[],
        unit="",
        formula="x",
        source_policy=[],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )
    md2 = MetricDefinition(
        metric_id="b",
        version="1.0.0",
        name="B",
        description="test",
        owner_email="eng@test.com",
        grain=[],
        unit="",
        formula="x",
        source_policy=[],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
        deprecation_status=MetricStatus.DEPRECATED,
    )
    reg.register(md1)
    reg.register(md2)
    active = reg.enumerate_active()
    assert len(active) == 1
    assert active[0].metric_id == "a"


def test_metric_catalog_is_alias() -> None:
    cat = MetricCatalog()
    assert isinstance(cat, MetricRegistry)
    assert cat.active_metric("missing") is None


def test_canonical_metrics_not_empty() -> None:
    assert len(CANONICAL_METRICS) > 0


# ── semantic metrictrax ───────────────────────────────────────


def test_validate_semver_transition_major_raises() -> None:
    with pytest.raises(GovernanceApprovalRequired):
        validate_semver_transition("1.0.0", "2.0.0", metric_id="test")


def test_validate_semver_transition_minor_ok() -> None:
    validate_semver_transition("1.0.0", "1.1.0")


def test_validate_semver_transition_invalid() -> None:
    with pytest.raises(ValueError):
        validate_semver_transition("1.0", "2.0.0")


# ── semantic point_in_time ────────────────────────────────────


def test_as_of_predicate() -> None:
    sql = as_of_predicate("2024-01-01T00:00:00Z")
    assert "effective_from" in sql
    assert "effective_to" in sql


def test_filter_as_of() -> None:
    records = [
        {
            "effective_from": "2024-01-01T00:00:00+00:00",
            "effective_to": "2024-06-01T00:00:00+00:00",
        },
        {"effective_from": "2024-06-01T00:00:00+00:00", "effective_to": None},
    ]
    assert len(filter_as_of(records, "2024-07-01T00:00:00Z")) == 1


# ── orchestration operators backfill ──────────────────────────


def test_validate_backfill_valid() -> None:
    req = BackfillRequest("dataset", "2023", "2024", "reason", "owner", "1.0.0", "small")
    valid, errors = validate_backfill(req)
    assert valid is True
    assert errors == []


def test_validate_backfill_invalid() -> None:
    req = BackfillRequest("dataset", "2024", "2023", "reason", "owner", "1.0.0", "small")
    valid, errors = validate_backfill(req)
    assert valid is False
    assert "start_period must be <= end_period" in errors


def test_validate_backfill_missing_reason() -> None:
    req = BackfillRequest("dataset", "2023", "2024", "", "owner", "1.0.0", "small")
    valid, errors = validate_backfill(req)
    assert valid is False
    assert any("reason is required" in e for e in errors)


def test_validate_backfill_bad_semver() -> None:
    req = BackfillRequest("dataset", "2023", "2024", "reason", "owner", "1.0", "small")
    valid, errors = validate_backfill(req)
    assert valid is False
    assert any("semver" in e for e in errors)


# ── orchestration backfill_orchestrator ───────────────────────


def test_backfill_orchestrator_submit_and_history() -> None:
    orch = BackfillOrchestrator()
    req = OrchestratorBackfillRequest(
        "dataset", "2023", "2024", "reason", "owner", "1.0.0", "small"
    )
    result = orch.submit(req)
    assert result["run_id"] == req.run_id
    assert len(result["idempotency_key"]) == 64
    assert result["validation_status"] == "PENDING"
    assert len(orch.history()) == 1
    assert orch.history()[0].dataset == "dataset"


def test_backfill_orchestrator_submit_invalid() -> None:
    orch = BackfillOrchestrator()
    req = OrchestratorBackfillRequest(
        "dataset", "2024", "2023", "reason", "owner", "1.0.0", "small"
    )
    with pytest.raises(BackfillValidationError):
        orch.submit(req)


# ── orchestration metrics ─────────────────────────────────────


def test_data_quality_metrics() -> None:
    m = DataQualityMetrics(freshness_lag_hours=1)
    assert m.is_fresh is True
    assert m.null_ratio == 0.0 or m.null_ratio is None
    m2 = DataQualityMetrics(freshness_lag_hours=25)
    assert m2.is_fresh is False
    m3 = DataQualityMetrics(freshness_lag_hours=None)
    assert m3.is_fresh is None


def test_pipeline_run_metrics_duration() -> None:
    now = dt.datetime.now(dt.UTC)
    m = PipelineRunMetrics("run", "pipeline", now)
    assert m.duration is None
    completed = dt.datetime.now(dt.UTC)
    m2 = PipelineRunMetrics("run", "pipeline", now, completed_at=completed)
    assert m2.duration is not None


# ── orchestration alerts ──────────────────────────────────────


def test_alert_record_targets() -> None:
    rec = AlertRecord("run", "pipeline", "dataset", "P0")
    assert len(rec.targets()) == 3
    assert rec.targets() == SEVERITY_MAP["P0"]


def test_route_alert() -> None:
    rec = AlertRecord("run", "pipeline", "dataset", "P0")
    targets = route_alert(rec)
    assert len(targets) == 3


# ── orchestration observability ───────────────────────────────


def test_emit_openmetadata_event() -> None:
    emit_openmetadata_event("run", "dataset", "SUCCESS")


def test_emit_cloudwatch_alarm() -> None:
    emit_cloudwatch_alarm({"run_id": "run"})


# ── orchestration run_state ───────────────────────────────────


def test_write_run_state() -> None:
    result = write_run_state(
        pipeline_id="pipeline",
        dataset_id="dataset",
        source_id="source",
        status="SUCCESS",
    )
    assert result["completed_at"]
    assert result["status"] == "SUCCESS"
    assert result["run_id"]


# ── orchestration cost ────────────────────────────────────────


def test_cost_telemetry_to_dict() -> None:
    t = CostTelemetry(run_id="r1", api_request_volume=10)
    d = t.to_dict()
    assert d["run_id"] == "r1"
    assert d["api_request_volume"] == 10


def test_dataset_cost_to_dict() -> None:
    t = DatasetCost(run_id="r1", dataset_id="d1")
    d = t.to_dict()
    assert d["dataset_id"] == "d1"


def test_record_cost_signal() -> None:
    t = CostTelemetry(run_id="r1")
    record_cost_signal(t)


def test_record_dataset_cost() -> None:
    t = DatasetCost(run_id="r1", dataset_id="d1")
    record_dataset_cost(t)


# ── orchestration tasks pure helpers ──────────────────────────


def test_validate_raw_valid() -> None:
    payload = b"data"
    import hashlib

    expected_hash = hashlib.sha256(payload).hexdigest()
    result = validate_raw(
        {
            "items": [
                {
                    "payload": payload,
                    "dataset_id": "d",
                    "metadata": type("M", (), {"content_hash": expected_hash})(),
                    "result": type("R", (), {"payload": payload})(),
                }
            ],
        }
    )
    assert result["status"] == "VALIDATED"


def test_validate_raw_invalid_hash() -> None:
    with pytest.raises(ValueError):
        validate_raw(
            {
                "items": [
                    {
                        "payload": b"data",
                        "dataset_id": "d",
                        "metadata": type("M", (), {"content_hash": "wrong"})(),
                        "result": type("R", (), {"payload": b"data"})(),
                    }
                ],
            }
        )


def test_canonical_silver() -> None:
    batch = {"run_id": "r", "source_id": "worldbank"}
    record = {
        "country_id": "USA",
        "indicator_id": "X",
        "observation_date": "2024",
        "value": 1.0,
        "unit": "usd",
        "source_id": "worldbank",
        "dataset_id": "d",
        "ingestion_timestamp": dt.datetime.now(dt.UTC),
        "payload_hash": "h",
    }
    out = _canonical_silver(record, batch)
    assert out["metric_id"] == "x"
    assert out["observation_date"] == "2024-01-01"


def test_run_silver_tests() -> None:
    result = run_silver_tests({"records": [{"observation_id": "x"}]})
    assert result["status"] == "SILVER_VALIDATED"


def test_build_gold() -> None:
    result = build_gold(
        {
            "records": [
                {
                    "effective_to": None,
                    "quality_status": "ACCEPTED",
                    "run_id": "r",
                    "observation_id": "x",
                    "effective_from": "2024-01-01",
                    "lineage_ref": "l",
                },
            ],
            "run_id": "r",
        }
    )
    assert result["status"] == "GOLD_BUILT"
    assert len(result["records"]) == 1


def test_publish_gold() -> None:
    result = publish_gold({"records": [{"a": 1}], "run_id": "r"})
    assert result["status"] == "PUBLISHED"
    assert result["records_written"] == 1


def test_publish_gold_empty_raises() -> None:
    with pytest.raises(ValueError):
        publish_gold({"records": []})


# ── orchestration dags klibra_pipeline ────────────────────────


def test_kibra_pipeline_dag_instance() -> None:
    from orchestration.dags.klibra_pipeline import DAG_ID

    assert DAG_ID == "klibra_pipeline"


def test_kibra_pipeline_fallback_classes() -> None:
    from orchestration.dags.klibra_pipeline import (
        TriggerRule,
    )

    assert TriggerRule.ALL_DONE == "all_done"


# ── intelligence composite ────────────────────────────────────


def test_methodology_version_bump_required() -> None:
    exc = MethodologyVersionBumpRequired("msg", expected_version="2.0.0")
    assert exc.expected_version == "2.0.0"


def test_intelligence_score_band_value() -> None:
    s = IntelligenceScore(
        product_id="p",
        methodology_version="1.0.0",
        score=50.0,
        confidence=0.5,
        coverage_ratio=0.5,
        input_snapshot_id="x",
        components={},
        contributions={},
        weights={},
    )
    assert s.score_band_value == "MEDIUM"
    s2 = IntelligenceScore(
        product_id="p",
        methodology_version="1.0.0",
        score=20.0,
        confidence=0.1,
        coverage_ratio=0.1,
        input_snapshot_id="x",
        components={},
        contributions={},
        weights={},
    )
    assert s2.score_band_value == "LOW"
    s3 = IntelligenceScore(
        product_id="p",
        methodology_version="1.0.0",
        score=90.0,
        confidence=0.9,
        coverage_ratio=0.9,
        input_snapshot_id="x",
        components={},
        contributions={},
        weights={},
    )
    assert s3.score_band_value == "HIGH"


def test_intelligence_score_band() -> None:
    assert CompositeScorer._band(20.0) == "LOW"
    assert CompositeScorer._band(50.0) == "MEDIUM"
    assert CompositeScorer._band(90.0) == "HIGH"


def test_composite_scorer_score() -> None:
    class _S(CompositeScorer):
        product_id = "test"
        methodology_version = "1.0.0"
        weights = {"a": 1.0}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

    scorer = _S()
    result = scorer.score({"a": 50.0})
    assert result.score == 50.0
    assert result.product_id == "test_score" or result.product_id == "test"
    assert result.input_snapshot_id
    assert result.components == {"a": 50.0}


def test_composite_scorer_coverage_check() -> None:
    class _S(CompositeScorer):
        product_id = "test"
        methodology_version = "1.0.0"
        weights = {"a": 1.0, "b": 1.0}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

    scorer = _S()
    confidence, coverage = scorer.coverage_check({"a": 50.0})
    assert coverage == 0.5
    assert confidence == 0.5


def test_composite_scorer_normalize() -> None:
    class _S(CompositeScorer):
        product_id = "test"
        methodology_version = "1.0.0"
        weights = {"a": 1.0}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

    scorer = _S()
    assert scorer.normalize({"a": 10.0}) == {"a": 10.0}


def test_composite_scorer_aggregate() -> None:
    class _S(CompositeScorer):
        product_id = "test"
        methodology_version = "1.0.0"
        weights = {"a": 0.5, "b": 0.5}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

    scorer = _S()
    assert scorer.aggregate({"a": 50.0, "b": 50.0}) == 50.0


def test_composite_scorer_missing_coverage() -> None:
    class _S(CompositeScorer):
        product_id = "test"
        methodology_version = "1.0.0"
        weights = {"a": 1.0}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

        def aggregate(self, components: dict[str, float]) -> float:
            return 0.0

    scorer = _S()
    result = scorer.score({"b": 50.0})
    assert result.coverage_ratio == 0.0
    assert result.score == 0.0


def test_intelligence_store_and_persist() -> None:
    class _S(CompositeScorer):
        product_id = "test_score"
        methodology_version = "1.0.0"
        weights = {"a": 1.0}

        def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
            return inputs

    scorer = _S()
    store = IntelligenceStore()
    row = persist_score(
        scorer.score({"a": 50.0}), entity_id="US", observation_period="2024", store=store
    )
    assert row["metric_id"] == "test_score"
    assert len(store.components) == 1
