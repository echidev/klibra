"""FRED Bronze parser — TDD §8, FR-4..FR-6 (002-B).

Merges the FRED series metadata with the observations list into Bronze
records. The metadata is provided by the caller (the connector fetches
it via ``/fred/series/`` and passes it to this function).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from ingestion.connectors.fred import FredConnector
from ingestion.util.manifest import sha256_hex

__all__ = ["build_bronze_records"]

logger = logging.getLogger(__name__)


def build_bronze_records(
    *,
    source_id: str,
    series_id: str,
    raw_payload: bytes,
    metadata: dict[str, Any] | None,
    run_id: str,
    ingestion_timestamp: dt.datetime,
    raw_source_url: str,
) -> list[dict[str, Any]]:
    """Build Bronze records from a FRED observations payload.

    ``metadata`` is the dict returned by ``FredConnector._fetch_metadata``
    (the FRED ``/fred/series/`` response). May be ``None`` if metadata
    could not be retrieved; in that case the rows still parse but lack
    ``title`` / ``units`` / ``frequency`` metadata.
    """

    payload_hash = sha256_hex(raw_payload)
    parsed = FredConnector.parse_bronze(raw_payload, series_id, metadata or {})
    out: list[dict[str, Any]] = []
    for row in parsed:
        out.append(
            {
                "source_id": source_id,
                "dataset_id": series_id,
                "metric_id": row.get("metric_id", series_id),
                "run_id": run_id,
                "ingestion_timestamp": ingestion_timestamp.isoformat(),
                "payload_hash": payload_hash,
                "raw_source_url": raw_source_url,
                "frequency": row.get("frequency", ""),
                "title": row.get("title", ""),
                "units": row.get("units", ""),
                "seasonal_adjustment": row.get("seasonal_adjustment", ""),
                "observation_date": row.get("observation_date", ""),
                "value": row["value"],
                "realtime_start": row.get("realtime_start", ""),
                "realtime_end": row.get("realtime_end", ""),
            }
        )
    return out
