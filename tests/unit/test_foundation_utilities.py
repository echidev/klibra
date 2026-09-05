"""Coverage tests for shared foundation and operational utilities."""

from __future__ import annotations

import datetime as dt
import io
import json

import pytest

from ingestion.util.idempotency import (
    compute_idempotency_key,
    validate_idempotency_components,
)
from ingestion.util.logging import (
    StructuredLogger,
    configure_root_logging,
    timed,
    trace_context,
)
from ingestion.util.manifest import build_manifest, manifest_to_json, sha256_hex
from intelligence.composite import CompositeScorer
from intelligence.persist import IntelligenceStore, persist_score
from orchestration.alerts.router import AlertRecord, route_alert
from orchestration.metrics.data import DataQualityMetrics
from orchestration.metrics.pipeline import PipelineRunMetrics
from orchestration.operators.backfill import BackfillRequest, validate_backfill
from orchestration.util.observability import emit_cloudwatch_alarm, emit_openmetadata_event
from orchestration.util.run_state import write_run_state
from semantic.metrictrax import GovernanceApprovalRequired, validate_semver_transition
from semantic.point_in_time import as_of_predicate, filter_as_of
from transformation.quality.framework import QualityFramework, QualityOutcome


class TruthyStringIO(io.StringIO):
    def __bool__(self) -> bool:
        return True


def test_manifest_and_idempotency_utilities() -> None:
    payload = b"payload"
    digest = sha256_hex(payload)
    assert len(digest) == 64
    assert validate_idempotency_components("source", "dataset", "2024", None, digest) == []
    assert validate_idempotency_components("", "dataset", "2024", None, digest)
    assert compute_idempotency_key(
        "source", "dataset", "2024", None, digest
    ) == compute_idempotency_key("source", "dataset", "2024", None, digest)
    manifest = build_manifest(
        source_id="source",
        dataset_id="dataset",
        run_id="run",
        source_url="https://example.test",
        content_hash=digest,
    )
    assert json.loads(manifest_to_json(manifest))["content_hash"] == digest


def test_structured_logging_context_and_timing() -> None:
    stream = TruthyStringIO()
    configure_root_logging(stream=stream)
    logger = StructuredLogger("test")
    with (
        trace_context(trace_id="trace", run_id="run"),
        timed(logger, "finished", source_id="source", dataset_id="dataset"),
    ):
        logger.info("started")
    records = [json.loads(line) for line in stream.getvalue().splitlines() if line]
    assert records[0]["trace_id"] == "trace"
    assert records[-1]["duration_ms"] >= 0


def test_operational_helpers() -> None:
    assert route_alert(AlertRecord("run", "pipeline", "dataset", "P0")).__len__() == 3
    assert DataQualityMetrics(freshness_lag_hours=1).is_fresh is True
    assert DataQualityMetrics(freshness_lag_hours=25).is_fresh is False
    metrics = PipelineRunMetrics("run", "pipeline", dt.datetime.now(dt.UTC))
    assert metrics.duration is None
    assert write_run_state(
        pipeline_id="pipeline", dataset_id="dataset", source_id="source", status="SUCCESS"
    )["completed_at"]
    emit_openmetadata_event("run", "dataset", "SUCCESS")
    emit_cloudwatch_alarm({"run_id": "run"})


def test_quality_and_point_in_time_helpers() -> None:
    quality = QualityFramework()
    assert (
        quality.evaluate_batch(payload_present=True, schema_valid=True) == QualityOutcome.ACCEPTED
    )
    assert (
        quality.evaluate_record(value=1, type_valid=False, range_valid=True)
        == QualityOutcome.QUARANTINED
    )
    assert (
        quality.evaluate_dataset(duplicate_rate=0, completeness=0.9)
        == QualityOutcome.ACCEPTED_WARNING
    )
    assert quality.evaluate_business(reconciliation_diff=0) == QualityOutcome.ACCEPTED
    records = [
        {
            "effective_from": "2024-01-01T00:00:00+00:00",
            "effective_to": "2024-06-01T00:00:00+00:00",
        },
        {"effective_from": "2024-06-01T00:00:00+00:00", "effective_to": None},
    ]
    assert len(filter_as_of(records, "2024-07-01T00:00:00Z")) == 1
    assert "effective_from" in as_of_predicate("2024-01-01T00:00:00Z")


def test_idempotency_rejects_non_strings() -> None:
    with pytest.raises(TypeError):
        compute_idempotency_key("source", "dataset", "2024", None, 123)  # type: ignore[arg-type]


class TestScorer(CompositeScorer):
    product_id = "test_score"
    methodology_version = "1.0.0"
    weights = {"a": 1.0}

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        return inputs


def test_semantic_and_intelligence_helpers() -> None:
    with pytest.raises(GovernanceApprovalRequired):
        validate_semver_transition("1.0.0", "2.0.0", metric_id="test")
    validate_semver_transition("1.0.0", "1.1.0")
    score = TestScorer().score({"a": 50.0})
    store = IntelligenceStore()
    row = persist_score(score, entity_id="US", observation_period="2024", store=store)
    assert row["metric_id"] == "test_score"
    assert len(store.components) == 1


def test_backfill_validation() -> None:
    request = BackfillRequest("dataset", "2024", "2023", "reason", "owner", "1.0.0", "small")
    valid, errors = validate_backfill(request)
    assert not valid
    assert "start_period must be <= end_period" in errors
