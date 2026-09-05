"""Integration contract tests for network‑bound connectors using mocks."""

from __future__ import annotations

import json

import pytest

from ingestion.connectors.alphavantage import AlphaVantageConnector, AlphaVantageKeyError
from ingestion.connectors.base import HttpResponse
from ingestion.connectors.fred import FredConnector, FredKeyError
from ingestion.connectors.worldbank import WorldBankConnector

# ----- AlphaVantage -----

def test_alphavantage_extract_success(monkeypatch) -> None:
    def fake_send(request):
        return HttpResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=b'{"Global Quote": {"05. price": "123.45"}}',
            url="https://mocked.alphavantage.co/query",
        )
    monkeypatch.setattr("ingestion.connectors.alphavantage.send_request", fake_send)
    conn = AlphaVantageConnector(symbol="AAPL", api_key="testkey")
    result = conn.extract()
    assert isinstance(result.payload, bytes)
    data = json.loads(result.payload)
    assert "Global Quote" in data
    assert result.source_url.startswith("https://mocked.alphavantage.co/query")


def test_alphavantage_missing_key() -> None:
    with pytest.raises(AlphaVantageKeyError):
        AlphaVantageConnector(symbol="AAPL", api_key="")

# ----- Fred -----

def test_fred_extract_success(monkeypatch) -> None:
    def fake_send(request):
        if "/observations" in request.url:
            body = json.dumps({"observations": [{"date": "2024-01-01", "value": "123.45"}]})
            return HttpResponse(status_code=200, headers={}, body=body.encode(), url=request.url)
        if "/series" in request.url:
            body = json.dumps({"seriess": [{"title": "GDP", "frequency_short": "A", "units_short": "USD"}]})
            return HttpResponse(status_code=200, headers={}, body=body.encode(), url=request.url)
        raise RuntimeError("unexpected URL")
    monkeypatch.setattr("ingestion.connectors.fred.send_request", fake_send)
    conn = FredConnector(series_id="GDP", api_key="a" * 32)
    result = conn.extract()
    payload = json.loads(result.payload)
    # payload json contains observation list inside 'observations' key
    assert isinstance(payload, dict)
    assert "observations" in payload
    assert payload["observations"][0]["value"] == "123.45"
    assert "/observations" in result.source_url

def test_fred_invalid_key() -> None:
    with pytest.raises(FredKeyError):
        FredConnector(series_id="GDP", api_key="short")

# ----- WorldBank -----

def test_worldbank_build_url() -> None:
    conn = WorldBankConnector(dataset_id="NY.GDP.MKTP.CD")
    url = conn._build_url("NY.GDP.MKTP.CD", date_range="2020:2024", format="json")
    assert "NY.GDP.MKTP.CD" in url
    assert "date=2020%3A2024" in url
    assert f"per_page={conn.per_page}" in url

def test_worldbank_extract_success(monkeypatch) -> None:
    class FakeResp:
        def __init__(self):
            self.status_code = 200
            self.headers = {"Content-Type": "application/json", "ETag": "etag123"}
            self.content = b"[{}, [{}]]"
        def raise_for_status(self):
            pass
    def fake_get(url, headers=None, timeout=None):
        return FakeResp()
    monkeypatch.setattr("requests.get", fake_get)
    conn = WorldBankConnector(dataset_id="NY.GDP.MKTP.CD")
    result = conn.extract()
    assert result.payload == b"[{}, [{}]]"
    assert result.source_url.startswith(conn.base_url)
    # validate_response should not raise with this payload
    conn.validate_response(result.payload)
