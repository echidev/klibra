"""Per-run lineage record emitter — TDD §69.

Emits lineage records (run_id, payload_hash, etc.) to the OpenMetadata
metadata store and the PG ``lineage`` table (see ``infrastructure/postgres/migrations/V001__control_plane.sql``).

Parameters
----------
rid: lineage_id
run_id: pipeline run ID from the DAG
payload_hash: SHA-256 hash of the source payload
transform_version: transformation version (bronze → silver → gold)
semantic_metric_version: semantic metric version (from contract)
intelligence_methodology_version: intelligence methodology version
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

__all__ = ["emit_lineage_record"]


def emit_lineage_record(
    *,
    run_id: str,
    payload_hash: str | None = None,
    transform_version: str | None = None,
    semantic_metric_version: str | None = None,
    intelligence_methodology_version: str | None = None,
) -> dict[str, Any]:
    """Return a lineage record dict ready for insertion / ingestion."""
    return {
        "lineage_id": str(uuid.uuid4()),
        "run_id": run_id,
        "payload_hash": payload_hash,
        "transform_version": transform_version,
        "semantic_metric_version": semantic_metric_version,
        "intelligence_methodology_version": intelligence_methodology_version,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
    }
