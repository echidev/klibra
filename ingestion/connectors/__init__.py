"""Source connector package — implements the common connector interface
defined in TDD §13.1 and ADR-002.

Every concrete connector (World Bank, ECB SDMX, FRED, IMF, Alpha Vantage,
CoinGecko) extends :class:`SourceConnectorBase` and implements the six
lifecycle methods: discover, authenticate, extract, validate_response,
persist_raw, emit_metadata.
"""

from ingestion.connectors.base import (
    ConnectorCapability,
    ExtractionResult,
    SourceConnectorBase,
    SourceMetadata,
)

__all__ = [
    "ConnectorCapability",
    "ExtractionResult",
    "SourceConnectorBase",
    "SourceMetadata",
]
