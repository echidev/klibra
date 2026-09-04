"""Run-state tracking for KLIBRA pipelines — TDD §14, §33.

Records pipeline execution metadata for observability, audit, and incident
handling. Follows the run-state schema from TDD §14 and the control-plane
tables defined in ``infrastructure/postgres/migrations/V001__control_plane.sql``.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from ingestion.util.logging import log_event

__all__ = ["write_run_state"]


def write_run_state(
    *,
    pipeline_id: str,
    dataset_id: str,
    source_id: str | None,
    status: str,
    records_received: int | None = None,
    records_written: int | None = None,
    records_rejected: int | None = None,
    payload_hash: str | None = None,
    source_version: str | None = None,
    max_observation_date: str | None = None,
    min_observation_date: str | None = None,
    schema_version: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Return a run-record matching the ``run_history`` schema.

    In a live deployment this function upserts into PostgreSQL
    (``run_history`` table, TDD §39). The module is kept side-effect-free so
    it can be unit-tested and reused by both Airflow operators and the CLI.
    """

    rid = run_id or str(uuid.uuid4())
    now_iso = dt.datetime.now(dt.UTC).isoformat()
    terminal = status in ("SUCCESS", "FAILED", "QUARANTINED")

    record: dict[str, Any] = {
        "run_id": rid,
        "pipeline_id": pipeline_id,
        "dataset_id": dataset_id,
        "source_id": source_id,
        "status": status,
        "started_at": now_iso,
        "completed_at": now_iso if terminal else None,
        "records_received": records_received,
        "records_written": records_written,
        "records_rejected": records_rejected,
        "payload_hash": payload_hash,
        "source_version": source_version,
        "max_observation_date": max_observation_date,
        "min_observation_date": min_observation_date,
        "schema_version": schema_version,
        "error_type": error_type,
        "error_message": error_message,
    }

    log_event(
        level=20,  # logging.INFO
        message=f"pipeline run {rid} {status} for dataset {dataset_id}",
        service="klibra-pipeline",
        dataset_id=dataset_id,
        source_id=source_id,
        details={
            "run_id": rid,
            **{
                k: v
                for k, v in {
                    "records_received": records_received,
                    "records_written": records_written,
                    "records_rejected": records_rejected,
                    "payload_hash": payload_hash,
                    "error_type": error_type,
                    "error_message": error_message,
                }.items()
                if v is not None
            },
        },
    )
    return record
