from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ingestion.connectors.base import SourceConnectorBase


@dataclass(frozen=True)
class ConnectorRegistration:
    source_id: str
    display_name: str
    access_class: str
    connector_class: type[SourceConnectorBase]
    capabilities: tuple[str, ...] = ()


REGISTRY: dict[str, ConnectorRegistration] = {}


def register(reg: ConnectorRegistration) -> None:
    if reg.source_id in REGISTRY:
        msg = f"duplicate source_id {reg.source_id!r}"
        raise ValueError(msg)
    REGISTRY[reg.source_id] = reg


def get(source_id: str) -> ConnectorRegistration:
    try:
        return REGISTRY[source_id]
    except KeyError:
        msg = f"unknown source_id {source_id!r}"
        raise KeyError(msg) from None


def discover_all() -> list[str]:
    return sorted(REGISTRY)


def list_sources() -> list[ConnectorRegistration]:
    return [REGISTRY[k] for k in sorted(REGISTRY)]


def _bootstrap() -> None:
    from ingestion.connectors.alphavantage import AlphaVantageConnector
    from ingestion.connectors.coingecko import CoinGeckoConnector
    from ingestion.connectors.ecb import EcbSdmxConnector
    from ingestion.connectors.fred import FredConnector
    from ingestion.connectors.worldbank import WorldBankConnector

    for reg in [
        ConnectorRegistration("worldbank", "World Bank", "A", WorldBankConnector, ("discover", "extract")),
        ConnectorRegistration("fred", "FRED", "B", FredConnector, ("discover", "extract")),
        ConnectorRegistration("ecb", "ECB", "A", EcbSdmxConnector, ("discover", "extract")),
        ConnectorRegistration("alphavantage", "Alpha Vantage", "B", AlphaVantageConnector, ("discover", "extract")),
        ConnectorRegistration("coingecko", "CoinGecko", "B", CoinGeckoConnector, ("discover", "extract")),
    ]:
        REGISTRY[reg.source_id] = reg


_bootstrap()
