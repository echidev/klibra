"""Bronze transformation for World Bank Indicators.

Parses the raw JSON envelope into source-aligned records and attaches
ingestion metadata. Bronze preserves every received field; no business
interpretation is applied here (TDD §8).

Output schema (one row per record)::

    {
        "source_id": str,
        "dataset_id": str,
        "country_id": str,  # ISO2 (e.g. "USA")
        "country_iso3": str,  # ISO3 (e.g. "USA")
        "country_name": str,
        "indicator_id": str,  # e.g. "NY.GDP.MKTP.CD"
        "indicator_name": str,
        "observation_date": str,  # year as "YYYY"
        "value": float | None,
        "unit": str,
        "obs_status": str,
        "decimal": int,
        "ingestion_run_id": str,
        "ingestion_timestamp": str,
        "payload_hash": str,
        "raw_source_url": str,
    }
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

__all__ = ["build_bronze_records"]


def _coerce_value(value: Any) -> float | None:
    """World Bank returns ``None`` for missing observations."""

    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _coerce_decimal(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _build_payload_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_bronze_records(
    *,
    source_id: str,
    dataset_id: str,
    raw_payload: bytes,
    ingestion_run_id: str,
    ingestion_timestamp: dt.datetime,
    raw_source_url: str,
) -> list[dict[str, Any]]:
    """Parse the World Bank JSON envelope into Bronze records.

    Returns an empty list if the envelope is malformed or contains no
    observations. The caller logs the situation and routes to
    ``/quarantine/`` per TDD §23.
    """

    try:
        envelope = json.loads(raw_payload)
    except json.JSONDecodeError:
        return []

    if not isinstance(envelope, list) or len(envelope) < 2:
        return []

    metadata, records = envelope[0], envelope[1]
    if not isinstance(records, list):
        return []

    payload_hash = _build_payload_hash(raw_payload)
    ingestion_ts_iso = ingestion_timestamp.isoformat()
    default_decimal: int | None = None

    bronze: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        indicator = record.get("indicator") or {}
        country = record.get("country") or {}
        bronze.append(
            {
                "source_id": source_id,
                "dataset_id": dataset_id,
                "country_id": country.get("id") or "",
                "country_iso3": record.get("countryiso3code") or "",
                "country_name": country.get("value") or "",
                "indicator_id": indicator.get("id") or "",
                "indicator_name": indicator.get("value") or "",
                "observation_date": str(record.get("date") or ""),
                "value": _coerce_value(record.get("value")),
                "unit": record.get("unit") or "",
                "obs_status": record.get("obs_status") or "",
                "decimal": _coerce_decimal(record.get("decimal")) or default_decimal,
                "ingestion_run_id": ingestion_run_id,
                "ingestion_timestamp": ingestion_ts_iso,
                "payload_hash": payload_hash,
                "raw_source_url": raw_source_url,
                "page": (metadata or {}).get("page"),
                "per_page": (metadata or {}).get("per_page"),
                "total": (metadata or {}).get("total"),
            }
        )
    return bronze
