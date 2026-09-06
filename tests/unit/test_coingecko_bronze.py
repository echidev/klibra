"""Tests for transformation/bronze/coingecko.build_bronze_records (T040)."""

from __future__ import annotations

import datetime as dt

from transformation.bronze.coingecko import build_bronze_records


def _payload() -> bytes:
    return (
        b'{"bitcoin":{"usd":50000.5,"usd_market_cap":1000000,'
        b'"usd_24h_vol":50000,"usd_24h_change":1.25,"last_updated_at":1735689600}}'
    )


def test_build_bronze_records_emits_4_rows_for_one_coin() -> None:
    ts = dt.datetime(2025, 1, 1, tzinfo=dt.UTC)
    out = build_bronze_records(
        dataset_id="bitcoin",
        raw_payload=_payload(),
        source_id="coingecko",
        run_id="r1",
        ingestion_timestamp=ts,
        raw_source_url="https://api.coingecko.com",
    )
    metrics = sorted(r["metric_id"] for r in out)
    assert metrics == ["market_cap", "price_change_24h", "price_usd", "volume_24h"]
    assert all(r["source_id"] == "coingecko" for r in out)
    assert all(r["observation_date"] for r in out)
    assert all(r["payload_hash"] for r in out)


def test_build_bronze_records_empty_returns_empty() -> None:
    assert build_bronze_records(dataset_id="x", raw_payload=b"") == []


def test_build_bronze_records_invalid_json_returns_empty() -> None:
    assert build_bronze_records(dataset_id="x", raw_payload=b"not json") == []
