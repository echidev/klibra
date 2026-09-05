"""Unit tests for the FRED connector.

Covers FR-1..FR-10 of spec.md §002-B and SC-B-1..SC-B-6.
"""

from __future__ import annotations

import pytest

from ingestion.connectors.fred import FredConnector, FredKeyError


def test_fred_missing_api_key() -> None:
    with pytest.raises(FredKeyError, match="FRED_API_KEY is required"):
        FredConnector(series_id="GDPC1", api_key="")


def test_fred_malformed_api_key_wrong_length() -> None:
    with pytest.raises(FredKeyError, match="32 lowercase alphanum"):
        FredConnector(series_id="GDPC1", api_key="short")


def test_fred_malformed_api_key_uppercase() -> None:
    with pytest.raises(FredKeyError, match="32 lowercase alphanum"):
        FredConnector(series_id="GDPC1", api_key="ABCDEFGHIJKLMNOPQRSTUVWXYZ012345")


def test_fred_malformed_api_key_with_dash() -> None:
    with pytest.raises(FredKeyError, match="32 lowercase alphanum"):
        FredConnector(series_id="GDPC1", api_key="abcdabcdabcdabcdabcdabcdabcdab-d")


def test_fred_valid_api_key() -> None:
    key = "a" * 32
    c = FredConnector(series_id="GDPC1", api_key=key)
    assert c.api_key == key
    assert c.dataset_id == "GDPC1"


def test_fred_discover_lists_known_series() -> None:
    c = FredConnector(series_id="GDPC1", api_key="a" * 32)
    known = c.discover()
    assert "GDP" in known
    assert "GDPC1" in known
    assert "FEDFUNDS" in known
    assert len(known) >= 4


def test_fred_authenticate_returns_empty() -> None:
    c = FredConnector(series_id="GDPC1", api_key="a" * 32)
    assert c.authenticate() == {}


def test_fred_backfill_no_duplicates_determinstic_key() -> None:
    """Same series + period + source version + payload hash ⇒ same idempotency key."""
    from ingestion.util.idempotency import compute_idempotency_key
    from ingestion.util.manifest import sha256_hex

    payload = b'{"observations": [{"date":"2024-01-01","value":"23082.119"}]}'
    h = sha256_hex(payload)
    k1 = compute_idempotency_key("fred", "GDPC1", "2024-Q1", None, h)
    k2 = compute_idempotency_key("fred", "GDPC1", "2024-Q1", None, h)
    assert k1 == k2
    assert len(k1) == 64


def test_fred_parse_bronze_merges_metadata_and_observations() -> None:
    meta = {
        "title": "Real Gross Domestic Product",
        "units_short": "Bil. of Chn. 2017 Dollars",
        "frequency_short": "Q",
        "seasonal_adjustment_short": "SA",
    }
    payload = b'{"observations": [{"date":"2024-01-01","value":"23082.119","realtime_start":"2026-09-04","realtime_end":"2026-09-04"}]}'
    records = FredConnector.parse_bronze(payload, "GDPC1", meta)
    assert len(records) == 1
    r = records[0]
    assert r["title"] == "Real Gross Domestic Product"
    assert r["frequency"] == "Q"
    assert r["value"] == pytest.approx(23082.119)
    assert r["observation_date"] == "2024-01-01"


def test_fred_parse_bronze_skips_dot_values() -> None:
    """FRED uses '.' as the null sentinel; those rows are skipped."""
    payload = b'{"observations": [{"date":"2024-01-01","value":"."},{"date":"2024-04-01","value":"23111"}]}'
    records = FredConnector.parse_bronze(payload, "GDP", {})
    assert len(records) == 1
    assert records[0]["observation_date"] == "2024-04-01"
