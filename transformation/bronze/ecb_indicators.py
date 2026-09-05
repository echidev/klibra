"""ECB SDMX CSV → Bronze parser — TDD §8, FR-1..FR-10.

Maps the ECB SDMX 2.1 ``csvdata`` response into Bronze records with the
canonical observation grain. The parser is intentionally pure-Python
(``csv`` module) so it works without pandas in the local dev path.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Any

__all__ = ["build_bronze_records", "ecb_bronze_row"]

logger = logging.getLogger(__name__)

# Required columns in the ECB csvdata header. The ECB SDMX 2.1 spec
# guarantees these (and a few more). We are explicit so a header change
# surfaces as a contract test failure, not silent drift.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "KEY",
    "FREQ",
    "CURRENCY",
    "CURRENCY_DENOM",
    "EXR_TYPE",
    "EXR_SUFFIX",
    "TIME_PERIOD",
    "OBS_VALUE",
    "OBS_STATUS",
    "TITLE",
    "UNIT",
)


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_date(value: Any) -> str:
    if not value:
        return ""
    s = str(value).strip()
    # SDMX 2.1 time periods can be YYYY, YYYY-MM, YYYY-Qn, or YYYY-MM-DD.
    # Keep the raw string in ``observation_date``; consumers normalize downstream.
    return s


def ecb_bronze_row(
    *,
    source_id: str,
    dataset_id: str,
    raw: dict[str, Any],
    run_id: str,
    ingestion_timestamp: dt.datetime,
    payload_hash: str,
    raw_source_url: str,
) -> dict[str, Any]:
    """Project one CSV row into a Bronze record."""

    return {
        "source_id": source_id,
        "dataset_id": dataset_id,
        "run_id": run_id,
        "ingestion_timestamp": ingestion_timestamp.isoformat(),
        "payload_hash": payload_hash,
        "raw_source_url": raw_source_url,
        "frequency": raw.get("FREQ", ""),
        "currency": raw.get("CURRENCY", ""),
        "currency_denom": raw.get("CURRENCY_DENOM", ""),
        "exr_type": raw.get("EXR_TYPE", ""),
        "exr_suffix": raw.get("EXR_SUFFIX", ""),
        "observation_date": _coerce_date(raw.get("TIME_PERIOD")),
        "value": _coerce_float(raw.get("OBS_VALUE")),
        "unit": raw.get("UNIT", ""),
        "obs_status": raw.get("OBS_STATUS", ""),
        "title": raw.get("TITLE", ""),
    }


def build_bronze_records(
    *,
    source_id: str,
    dataset_id: str,
    raw_payload: bytes,
    run_id: str,
    ingestion_timestamp: dt.datetime,
    raw_source_url: str,
) -> list[dict[str, Any]]:
    """Build a list of Bronze records from an ECB SDMX csvdata payload.

    Skips rows with empty or non-numeric ``OBS_VALUE``. Returns an empty
    list (not an error) when the payload has no data rows.
    """

    from ingestion.util.manifest import sha256_hex

    payload_hash = sha256_hex(raw_payload)
    text = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else raw_payload
    reader = csv.DictReader(io.StringIO(text))

    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        logger.warning("ECB csvdata header missing columns: %s", missing)

    records: list[dict[str, Any]] = []
    for raw in reader:
        if raw.get("OBS_VALUE") in (None, ""):
            continue
        if _coerce_float(raw.get("OBS_VALUE")) is None:
            continue
        records.append(
            ecb_bronze_row(
                source_id=source_id,
                dataset_id=dataset_id,
                raw=raw,
                run_id=run_id,
                ingestion_timestamp=ingestion_timestamp,
                payload_hash=payload_hash,
                raw_source_url=raw_source_url,
            )
        )
    return records
