import pytest

from ingestion.connectors.alphavantage import AlphaVantageConnector, AlphaVantageKeyError
from ingestion.connectors.fred import FredConnector, FredKeyError


def test_worldbank_validate_access_ok():
    from ingestion.connectors.worldbank import WorldBankConnector

    c = WorldBankConnector(dataset_id="NY.GDP.MKTP.CD")
    c.validate_access()


def test_ecb_validate_access_ok():
    from ingestion.connectors.ecb import EcbSdmxConnector

    c = EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A")
    c.validate_access()


def test_fred_validate_access_missing(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    try:
        c = FredConnector(series_id="GDPC1", api_key="")
        assert False, "should have raised in __init__"
    except FredKeyError:
        pass


def test_alphavantage_validate_access_missing(monkeypatch):
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    try:
        c = AlphaVantageConnector(symbol="AAPL", api_key="")
        assert False, "should have raised in __init__"
    except AlphaVantageKeyError:
        pass


def test_coingecko_validate_access_ok():
    from ingestion.connectors.coingecko import CoinGeckoConnector

    c = CoinGeckoConnector(coin_id="bitcoin")
    c.validate_access()
