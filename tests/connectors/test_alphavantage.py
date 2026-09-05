"""Unit tests for the Alpha Vantage connector — FR-E-4 (T049)."""

from __future__ import annotations

import json

import pytest

from ingestion.connectors.alphavantage import AlphaVantageConnector, AlphaVantageKeyError


def test_av_missing_api_key() -> None:
    with pytest.raises(AlphaVantageKeyError, match="ALPHAVANTAGE_API_KEY is required"):
        AlphaVantageConnector(symbol="IBM", api_key="")


def test_av_valid_api_key() -> None:
    c = AlphaVantageConnector(symbol="IBM", api_key="anykeyworks")
    assert c.dataset_id == "IBM"
    assert c.api_key == "anykeyworks"
    assert c.function == "GLOBAL_QUOTE"


def test_av_authenticate_returns_empty() -> None:
    c = AlphaVantageConnector(symbol="IBM", api_key="anykeyworks")
    assert c.authenticate() == {}


def test_av_extract_raises_on_error_message(monkeypatch) -> None:
    from ingestion.connectors import alphavantage as av_mod

    payload = json.dumps(
        {"Error Message": "Invalid API call. Please retry or visit the documentation."}
    ).encode()
    response = type("R", (), {"status_code": 200, "headers": {}, "body": payload, "url": "x"})()
    monkeypatch.setattr(av_mod, "send_request", lambda *a, **k: response)
    c = AlphaVantageConnector(symbol="IBM", api_key="anykeyworks")
    with pytest.raises(ValueError, match="Alpha Vantage returned error"):
        c.extract()


def test_av_rate_limit_is_low_free_tier() -> None:
    """Free tier is 5 req/min, 25 req/day. We expect a low rate limit policy."""
    AlphaVantageConnector(symbol="IBM", api_key="anykeyworks")
    # The connector should self-declare a low rate limit (5 rpm free).
    # Implementation: enforce low limit via retries on 429.
    # This test verifies the constant, not a live call.
    from ingestion.connectors.alphavantage import AV_RATE_LIMIT_RPM

    assert AV_RATE_LIMIT_RPM <= 10
