"""Bronze parser for CoinGecko market observations.

Canonical shape per ``contracts/discovery.md``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any


def build_bronze_records(
    *,
    dataset_id: str,
    raw_payload: bytes,
    source_id: str = "coingecko",
    run_id: str = "",
    ingestion_timestamp: dt.datetime | None = None,
    raw_source_url: str = "",
) -> list[dict[str, Any]]:
    """Parse CoinGecko ``/simple/price`` response into Bronze rows."""
    if not raw_payload:
        return []
    try:
        body: dict[str, Any] = json.loads(raw_payload)
    except (json.JSONDecodeError, ValueError):
        return []

    ts = ingestion_timestamp or dt.datetime.now(tz=dt.UTC)
    iso_date = ts.date().isoformat()
    payload_hash = hashlib.sha256(raw_payload).hexdigest()

    records: list[dict[str, Any]] = []
    if not isinstance(body, dict):
        return []
    for coin_id, metrics in body.items():
        if not isinstance(metrics, dict):
            continue
        mcap = metrics.get("usd_market_cap")
        vol = metrics.get("usd_24h_vol")
        change = metrics.get("usd_24h_change")
        price = metrics.get("usd")
        last_updated = metrics.get("last_updated_at")
        if last_updated:
            try:
                obs_date = (
                    dt.datetime.fromtimestamp(int(last_updated), tz=dt.UTC).date().isoformat()
                )
            except Exception:
                obs_date = iso_date
        else:
            obs_date = iso_date
        base: dict[str, Any] = {
            "source_id": source_id,
            "dataset_id": dataset_id,
            "run_id": run_id,
            "ingestion_timestamp": ts,
            "raw_source_url": raw_source_url,
            "coin_id": coin_id,
            "observation_date": obs_date,
            "payload_hash": payload_hash,
        }
        if price is not None:
            records.append({**base, "metric_id": "price_usd", "value": float(price), "unit": "USD"})
        if mcap is not None:
            records.append({**base, "metric_id": "market_cap", "value": float(mcap), "unit": "USD"})
        if vol is not None:
            records.append({**base, "metric_id": "volume_24h", "value": float(vol), "unit": "USD"})
        if change is not None:
            records.append(
                {**base, "metric_id": "price_change_24h", "value": float(change), "unit": "percent"}
            )
    return records
