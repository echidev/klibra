"""Coverage tests for ECB and FRED connectors."""

from __future__ import annotations

import pytest

from ingestion.connectors.ecb import EcbSdmxConnector
from ingestion.connectors.fred import FredConnector, FredKeyError


def test_ecb_connector_init_discover_authenticate() -> None:
    conn = EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A")
    assert conn.source_id == "ecb"
    assert conn.discover() == ["EXR", "FM", "IRS", "BSI", "MIR", "Yc"]
    assert conn.authenticate() == {}
    assert conn.connector_version == "1.0.0"


def test_ecb_split_dataset_id() -> None:
    assert EcbSdmxConnector._split_dataset_id("EXR.M.USD.EUR.SP00.A") == ("EXR", "M.USD.EUR.SP00.A")
    assert EcbSdmxConnector._split_dataset_id("EXR..USD.EUR.SP00.A") == ("EXR", "?.USD.EUR.SP00.A")
    assert EcbSdmxConnector._split_dataset_id("EXR") == ("EXR", None)


def test_ecb_frequency_hint() -> None:
    assert EcbSdmxConnector._frequency_hint("EXR.M.USD.EUR.SP00.A") == "M"
    assert EcbSdmxConnector._frequency_hint("EXR..USD.EUR.SP00.A") == "?"
    assert EcbSdmxConnector._frequency_hint("EXR") == "M"


def test_ecb_parse_bronze_valid() -> None:
    payload = b"""KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,OBS_VALUE,TIME_PERIOD
A,EXR,M,USD,EUR,SP00,2.5,2024-01-01
"""
    result = EcbSdmxConnector.parse_bronze(payload, "EXR.M.USD.EUR.SP00.A")
    assert len(result) == 1
    assert result[0]["value"] == 2.5
    assert result[0]["source_id"] == "ecb"
    assert result[0]["dataset_id"] == "EXR.M.USD.EUR.SP00.A"


def test_ecb_parse_bronze_empty() -> None:
    assert EcbSdmxConnector.parse_bronze(b"", "EXR") == []


def test_fred_connector_init_key_validation() -> None:
    with pytest.raises(FredKeyError):
        FredConnector(series_id="GDP", api_key="")
    with pytest.raises(FredKeyError):
        FredConnector(series_id="GDP", api_key="invalid")
    assert FredConnector(series_id="GDP", api_key="a" * 32).api_key == "a" * 32


def test_fred_connector_discover() -> None:
    conn = FredConnector(series_id="GDP", api_key="a" * 32)
    assert "GDP" in conn.discover()
    assert "FEDFUNDS" in conn.discover()


def test_fred_connector_validate_key() -> None:
    # missing key
    with pytest.raises(FredKeyError):
        FredConnector(series_id="GDP")
    # too short
    with pytest.raises(FredKeyError):
        FredConnector(series_id="GDP", api_key="short")


def test_fred_parse_bronze() -> None:
    payload = b'{"observations": [{"date": "2024-01-01", "value": "5.2", "realtime_start": "", "realtime_end": ""}]}'
    result = FredConnector.parse_bronze(payload, "GDP")
    assert len(result) == 1
    assert result[0]["source_id"] == "fred"
    assert result[0]["metric_id"] == "gdp_growth_rate"
    assert result[0]["value"] == 5.2


def test_fred_parse_bronze_empty() -> None:
    assert FredConnector.parse_bronze(b"{}", "GDP") == []


def test_fred_parse_bronze_skip_missing() -> None:
    payload = b'{"observations": [{"date": "2024-01-01", "value": "."}]}'
    assert FredConnector.parse_bronze(payload, "GDP") == []
