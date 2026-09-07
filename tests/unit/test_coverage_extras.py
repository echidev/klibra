"""Extra unit tests to raise line coverage to 90 %.

Targets the cheapest branches not exercised by the existing test set:
- ``backfill_cli.main`` (both success and validation-rejection paths)
- ``orchestration.operators.backfill_orchestrator.BackfillOrchestrator.submit``
  / ``.history`` and ``BackfillValidationError``
- ``orchestration.metrics.pipeline.Counter`` mutations + ``PipelineRunMetrics.duration``
- ``orchestration.util.storage`` factory error branches
- ``ingestion.storage.raw.LocalStorageWriter.ensure_bucket`` happy and
  "bucket already exists" paths and ``RawStorageWriter._assert_absent``
  happy / raises / no-attr paths
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest


# ── backfill_cli.main ─────────────────────────────────────────────


def test_backfill_cli_main_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from orchestration.operators import backfill_cli

    args = [
        "--dataset",
        "worldbank:EXR",
        "--start",
        "2024-01-01",
        "--end",
        "2024-01-07",
        "--reason",
        "re-extract",
        "--requested-by",
        "alice@example",
        "--code-version",
        "0.1.0",
        "--expected-impact",
        "minor",
    ]
    rc = backfill_cli.main(args)
    assert rc == 0


def test_backfill_cli_main_rejected(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    from orchestration.operators import backfill_cli

    args = [
        "--dataset",
        "worldbank:EXR",
        "--start",
        "2024-01-07",
        "--end",
        "2024-01-01",  # inverted range → validation fails
        "--reason",
        "x",
        "--requested-by",
        "alice",
        "--code-version",
        "0.1.0",
        "--expected-impact",
        "minor",
    ]
    rc = backfill_cli.main(args)
    assert rc == 1
    captured = capsys.readouterr()
    body = json.loads(captured.out)
    assert body["status"] == "REJECTED"
    assert body["errors"]


# ── BackfillOrchestrator.submit / history / BackfillValidationError ──


def test_backfill_orchestrator_submit_and_history() -> None:
    from orchestration.operators.backfill_orchestrator import (
        BackfillOrchestrator,
        BackfillRequest,
        BackfillValidationError,
    )

    orch = BackfillOrchestrator()
    assert orch.history() == []

    req = BackfillRequest(
        dataset="worldbank:EXR",
        start_period="2024-01-01",
        end_period="2024-01-07",
        reason="r",
        requested_by="alice",
        code_version="0.1.0",
        expected_impact="minor",
    )
    receipt = orch.submit(req)
    assert receipt["run_id"] == req.run_id
    assert receipt["idempotency_key"]
    assert orch.history()[0] is req


def test_backfill_orchestrator_submit_invalid() -> None:
    from orchestration.operators.backfill_orchestrator import (
        BackfillOrchestrator,
        BackfillRequest,
        BackfillValidationError,
    )

    bad = BackfillRequest(
        dataset="x",
        start_period="2024-01-01",
        end_period="2024-01-07",
        reason="",
        requested_by="alice",
        code_version="0.1.0",
        expected_impact="minor",
    )
    with pytest.raises(BackfillValidationError):
        BackfillOrchestrator().submit(bad)


# ── metrics.pipeline.Counter and PipelineRunMetrics.duration ────────


def test_counter_inc_dec_reset_value_repr() -> None:
    from orchestration.metrics.pipeline import Counter, PipelineRunMetrics

    c = Counter()
    assert c.value == 0
    c.inc()
    c.inc(2)
    assert c.value == 3
    c.dec()
    assert c.value == 2
    assert repr(c) == "Counter(2)"
    c.reset()
    assert c.value == 0


def test_pipeline_run_metrics_duration_property() -> None:
    import datetime as dt

    from orchestration.metrics.pipeline import PipelineRunMetrics

    started = dt.datetime(2024, 1, 1, 0, 0, 0, tzinfo=dt.UTC)
    completed = dt.datetime(2024, 1, 1, 0, 1, 0, tzinfo=dt.UTC)
    m = PipelineRunMetrics(
        run_id="r", pipeline_id="p", started_at=started, completed_at=completed
    )
    assert m.duration == 60.0

    incomplete = PipelineRunMetrics(run_id="r", pipeline_id="p", started_at=started)
    assert incomplete.duration is None

    fallback = PipelineRunMetrics(
        run_id="r",
        pipeline_id="p",
        started_at=started,
        duration_seconds=12.5,
    )
    assert fallback.duration == 12.5


# ── orchestration.util.storage factory error branches ──────────────


def test_make_storage_writer_development_missing_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestration.util import storage

    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MINIO_ACCESS_KEY"):
        storage.make_storage_writer()


def test_make_storage_writer_production(monkeypatch: pytest.MonkeyPatch) -> None:
    from orchestration.util import storage

    monkeypatch.delenv("KLIBRA_ENV", raising=False)
    monkeypatch.setenv("AWS_S3_BUCKET_RAW", "klibra-test-raw")
    writer = storage.make_storage_writer()
    from ingestion.storage.raw import CloudStorageWriter

    assert isinstance(writer, CloudStorageWriter)
    assert writer.bucket_name == "klibra-test-raw"


def test_make_storage_client_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestration.util import storage

    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "x")
    monkeypatch.setenv("MINIO_SECRET_KEY", "y")
    client = storage.make_storage_client()
    # Minio instance is returned; not a real connection until used.
    assert client is not None


def test_make_storage_client_development_missing_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestration.util import storage

    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MINIO_ACCESS_KEY"):
        storage.make_storage_client()


# ── ingestion.storage.raw: _assert_absent + ensure_bucket ───────────


def test_assert_absent_raises_when_existing() -> None:
    from ingestion.storage.raw import RawStorageWriter

    writer = RawStorageWriter("bucket")

    class _Client:
        def stat_object(self, bucket: str, key: str) -> None:  # noqa: D401
            return None

    with pytest.raises(FileExistsError):
        writer._assert_absent(_Client(), "raw/obj")


def test_assert_absent_swallows_underlying_error() -> None:
    from ingestion.storage.raw import RawStorageWriter

    writer = RawStorageWriter("bucket")

    class _Client:
        def stat_object(self, bucket: str, key: str) -> None:
            raise OSError("boom")

    # No raise: underlying object-store error is treated as "absent"
    assert writer._assert_absent(_Client(), "raw/obj") is None


def test_assert_absent_no_relevant_attr_returns() -> None:
    from ingestion.storage.raw import RawStorageWriter

    writer = RawStorageWriter("bucket")

    class _Client:
        pass

    assert writer._assert_absent(_Client(), "raw/obj") is None


def test_local_storage_writer_ensure_bucket_happy() -> None:
    from ingestion.storage.raw import LocalStorageWriter

    writer = LocalStorageWriter("bucket")
    client = MagicMock()
    client.bucket_exists.return_value = True
    writer.ensure_bucket(client)
    client.bucket_exists.assert_called_once_with("bucket")
    client.make_bucket.assert_not_called()


def test_local_storage_writer_ensure_bucket_creates() -> None:
    from ingestion.storage.raw import LocalStorageWriter

    writer = LocalStorageWriter("bucket")
    client = MagicMock()
    client.bucket_exists.return_value = False
    writer.ensure_bucket(client)
    client.make_bucket.assert_called_once_with("bucket")
