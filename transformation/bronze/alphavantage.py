"""Alpha Vantage Bronze parser — TDD §8, FR-7 (003).

Maps the Alpha Vantage ``GLOBAL_QUOTE`` and ``TIME_SERIES_*`` payloads
into source-aligned Bronze records. The connector returns raw ``bytes``
for the JSON payload; this module normalizes it into the canonical
Bronze dict with fields matching ``ecb_indicators``/``worldbank_indicators``.

Output columns
--------------
- ``source_id``, ``dataset_id`` (from the extraction context).
- ``instrument_id`` — from ``01. symbol`` inside ``Global Quote``.
- ``observation_date`` — ISO ``YYYY-MM-DD`` from the quote's ``07. latest trading day``.
- ``value`` — float from ``05. price`` (or first ``4. close`` for TIME_SERIES).
- ``unit`` — ``USD`` (default) or ``price``.
- Standard run-identity columns: ``run_id``, ``ingestion_timestamp``, ``payload_hash``, ``raw_source_url``.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

__all__ = ["build_bronze_records"]

logger = logging.getLogger(__name__)


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_global_quote(data: dict[str, Any]) -> tuple[str, float | None, str, str]:
    """Extract (instrument_id, value, observation_date) from a ``Global Quote`` payload.

    Returns
    -------
    instrument_id, value, observation_date, title
    """

    quote = data.get("Global Quote") or {}
    # Alpha Vantage GLOBAL_QUOTE uses "01. symbol" etc.
    symbol = quote.get("01. symbol", "")
    price = _coerce_float(quote.get("05. price"))
    date = str(quote.get("07. latest trading day", "")).strip()
    return (symbol, price, date, symbol)


def _parse_time_series(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract rows from a ``Time Series (Daily)`` or ``TIME_SERIES_*`` payload.

    Returns a list of ``{"observation_date": ISO, "value": float, "title": symbol}``.
    """

    rows: list[dict[str, Any]] = []
    # The time-series key is provider-formatted, e.g. ``"Time Series (Daily)"``.
    meta = data.get("Meta Data") or {}
    symbol = meta.get("2. Symbol") or meta.get("1: Symbol") or ""
    for payload_key, time_series in data.items():
        if not isinstance(time_series, dict):
            continue
        if "Meta Data" in payload_key:
            continue
        # First key that looks like a date-keyed map is the series.
        for date_str, day in time_series.items() if isinstance(time_series, dict) else []:  # type: ignore[union-attr]
            val = _coerce_float(day.get("4. close") or day.get("close"))
            rows.append(
                {
                    "instrument_id": symbol,
                    "observation_date": str(date_str).strip(),
                    "value": val,
                    "title": symbol,
                }
            )
        if rows:
            break
    return rows


def build_bronze_records(
    *,
    source_id: str,
    dataset_id: str,
    raw_payload: bytes,
    run_id: str,
    ingestion_timestamp: dt.datetime,
    raw_source_url: str,
) -> list[dict[str, Any]]:
    """Build Alpha Vantage Bronze records.

    Parameters
    ----------
    source_id: str
        ``"alphavantage"``.
    dataset_id: str
        dataset identifier (dataset segment after the ``:``, e.g. ``GLOBAL_QUOTE:AAPL``).
    raw_payload: bytes
        Raw JSON bytes from the Alpha Vantage ``extract()`` call.
    run_id: str
        Run identifier (ECB.run_id‑encoded, not a new uuid).
    ingestion_timestamp: datetime
        Ingestion time (ECB run time).
    raw_source_url: str
        Raw source URL.

    Returns
    -------
    list[dict]
        List of Bronze records; ``[]`` if no parseable data.
    """

    from ingestion.util.manifest import sha256_hex

    payload_hash = sha256_hex(raw_payload)
    ingestion_ts_iso = ingestion_timestamp.isoformat()

    try:
        data: dict[str, Any] = json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.warning("Alpha Vantage payload is not valid JSON for dataset %r", dataset_id)
        return []

    # Branch: GLOBAL_QUOTE vs TIME_SERIES
    instrument_id: str
    value: float | None
    observation_date: str
    title: str
    rows: list[dict[str, Any]] = []

    if "Global Quote" in data:
        instrument_id, value, observation_date, title = _parse_global_quote(data)
        if observation_date and value is not None:
            rows.append(
                {
                    "instrument_id": instrument_id,
                    "observation_date": observation_date,
                    "value": value,
                    "title": title,
                }
            )
    elif any("Time Series" in k for k in data):
        parsed = _parse_time_series(data)
        rows.extend(parsed)

    bronze: list[dict[str, Any]] = []
    for row in rows:
        if row.get("value") is None or not row.get("observation_date"):
            continue
        bronze.append(
            {
                "source_id": source_id,
                "dataset_id": dataset_id,
                "instrument_id": row.get("instrument_id", ""),
                "observation_date": str(row["observation_date"]),
                "value": float(row["value"]),  # type: ignore[typeddict-item]
                "unit": "price",
                "title": str(row.get("title", "")),
                "frequency": str(dataset_id).split(":")[0]
                if ":" in dataset_id
                else str(dataset_id),
                "run_id": run_id,
                "ingestion_timestamp": ingestion_ts_iso,
                "payload_hash": payload_hash,
                "raw_source_url": raw_source_url,
                # Normalise FRED/ECB-like columns names for _canonical_silver compatibility
                "country_id": str(row.get("instrument_id", "")),
                "indicator_id": str(dataset_id),
            }
        )
    return bronze
