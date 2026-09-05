"""Coverage tests for AlphaVantage, WorldBank, and storage helpers."""

from __future__ import annotations

import pytest

from ingestion.connectors.alphavantage import AlphaVantageConnector, AlphaVantageKeyError
from ingestion.connectors.worldbank import WorldBankConnector
from ingestion.storage.schema_fingerprint import (
    SchemaFingerprint,
    SchemaFingerprintStore,
    classify_schema_change,
    fingerprint_payload,
)


def test_alphavantage_connector_key_validation() -> None:
    with pytest.raises(AlphaVantageKeyError):
        AlphaVantageConnector(symbol="AAPL", api_key="")
    conn = AlphaVantageConnector(symbol="AAPL", api_key="test_key_123")
    assert conn.api_key == "test_key_123"
    assert conn.connector_version == "1.0.0"


def test_alphavantage_connector_defaults() -> None:
    conn = AlphaVantageConnector(symbol="AAPL", api_key="key")
    assert conn.base_url == "https://www.alphavantage.co/query"
    assert conn.function == "GLOBAL_QUOTE"


def test_worldbank_connector_discover_and_build_url() -> None:
    conn = WorldBankConnector(dataset_id="NY.GDP.MKTP.CD")
    indicators = conn.discover()
    assert "NY.GDP.MKTP.CD" in indicators
    assert "NY.GDP.MKTP.KD.ZG" in indicators
    url = conn._build_url("NY.GDP.MKTP.CD")
    assert "/country/all/indicator/NY.GDP.MKTP.CD" in url
    assert "per_page=10000" in url


def test_worldbank_connector_build_url_with_date() -> None:
    conn = WorldBankConnector()
    url = conn._build_url("NY.GDP.MKTP.CD", date_range="2020:2024", format="json")
    assert "date=2020%3A2024" in url


def test_schema_fingerprint_flatten() -> None:
    result = fingerprint_payload(b'{"a": {"b": 1}, "c": [1, 2]}')
    assert result["a.b"] == "int"
    assert result["c"] == "array:int"


def test_schema_fingerprint_opaque() -> None:
    result = fingerprint_payload(b"not json")
    assert result == {"__opaque__": "bytes"}


def test_schema_fingerprint_classify() -> None:
    old: dict[str, str] = {"a": "int", "b": "str"}
    assert classify_schema_change(old, {"a": "int", "b": "str"}) == "COMPATIBLE"
    assert (
        classify_schema_change(old, {"a": "int", "b": "str", "c": "bool"}) == "POTENTIALLY_BREAKING"
    )
    assert classify_schema_change(old, {"a": "float", "b": "str"}) == "POTENTIALLY_BREAKING"
    assert classify_schema_change(old, {"a": "int"}) == "BREAKING"


def test_schema_fingerprint_store_record() -> None:
    store = SchemaFingerprintStore()
    fp1 = store.record(source_id="s", dataset_id="d", run_id="r1", payload=b'{"a": 1}')
    assert fp1.change_class == "COMPATIBLE"
    fp2 = store.record(source_id="s", dataset_id="d", run_id="r2", payload=b'{"a": 1}')
    assert fp2.change_class == "COMPATIBLE"
    assert store.latest("s", "d") is not None
    assert store.latest("missing", "d") is None


def test_schema_fingerprint_store_schema() -> None:
    store = SchemaFingerprintStore()
    fp = store.record(source_id="s", dataset_id="d", run_id="r1", payload=b'{"a": 1}')
    assert isinstance(fp, SchemaFingerprint)
    assert fp.hash
    assert fp.created_at
