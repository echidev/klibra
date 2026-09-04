"""World Bank Indicators API connector — TDD §13, PRD §10.1, ADR-002.

Public API, no credential required (Access Class A). Returns JSON envelopes of
the form::

    [
      {"page": 1, "pages": 1, "per_page": "100", "total": 1},
      [
        {"indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
         "country": {"id": "USA", "value": "United States"},
         "countryiso3code": "USA",
         "date": "2023",
         "value": 27360900000000.0,
         "unit": "",
         "obs_status": "",
         "decimal": 0}
      ]
    ]

The connector normalizes each record to a source-aligned dict, attaches
acquisition metadata via :meth:`SourceConnectorBase.emit_metadata`, and
defers persistence to the orchestration layer.
"""

from __future__ import annotations

import datetime as dt
import logging
import urllib.parse
from typing import Any

import requests

from ingestion.connectors.base import (
    ExtractionResult,
    SourceConnectorBase,
)

__all__ = ["WorldBankConnector"]

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.worldbank.org/v2"
DEFAULT_PER_PAGE = 10000
CONNECTOR_VERSION = "1.0.0"


class WorldBankConnector(SourceConnectorBase):
    """Connector for the World Bank Indicators V2 API.

    Parameters
    ----------
    source_id:
        Defaults to ``"worldbank"``.
    dataset_id:
        World Bank indicator id, e.g. ``"NY.GDP.MKTP.CD"`` or
        ``"all"`` for the catalog.
    base_url:
        Override for non-default deployments.
    per_page:
        Page size; defaults to the API maximum.
    timeout:
        HTTP timeout in seconds.
    """

    connector_version: str = CONNECTOR_VERSION

    def __init__(
        self,
        dataset_id: str = "all",
        *,
        source_id: str = "worldbank",
        base_url: str = DEFAULT_BASE_URL,
        per_page: int = DEFAULT_PER_PAGE,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(source_id=source_id, dataset_id=dataset_id)
        self.base_url = base_url.rstrip("/")
        self.per_page = per_page
        self.timeout = timeout

    def discover(self) -> list[str]:
        """Enumerate a small set of well-known Release 1 indicators.

        The full catalog is large; the canonical set is documented in the
        source catalog (``docs/data/source_catalog.yaml``). For on-the-fly
        discovery prefer the public Sources API; this method exists to
        satisfy the connector interface.
        """
        return [
            "NY.GDP.MKTP.CD",  # GDP (current US$)
            "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
            "FP.CPI.TOTL.ZG",  # Inflation, consumer prices (annual %)
            "SL.UEM.TOTL.ZS",  # Unemployment (% of total labor force)
            "FR.INR.RINR",  # Real interest rate (%)
        ]

    def authenticate(self) -> dict[str, str]:
        """World Bank API requires no auth. Return empty headers."""
        return {}

    def _build_url(
        self,
        indicator: str,
        *,
        date_range: str | None = None,
        per_page: int | None = None,
        format: str = "json",
    ) -> str:
        path = f"/country/all/indicator/{indicator}"
        params: dict[str, str] = {
            "format": format,
            "per_page": str(per_page or self.per_page),
        }
        if date_range:
            params["date"] = date_range
        return f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"

    def extract(
        self,
        *,
        date_range: str | None = None,
        format: str = "json",
    ) -> ExtractionResult:
        """Fetch one indicator (or the catalog when ``dataset_id == 'all'``).

        Parameters
        ----------
        date_range:
            Optional ``"YYYY:YYYY"`` range. Defaults to all available years.
        format:
            API response format. ``"json"`` (default) or ``"xml"``.
        """

        url = self._build_url(self.dataset_id, date_range=date_range, format=format)
        logger.info(
            "worldbank request source=%s indicator=%s url=%s",
            self.source_id,
            self.dataset_id,
            url,
        )
        response = requests.get(url, headers=self.authenticate(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.content
        self.validate_response(payload)

        return ExtractionResult(
            payload=payload,
            source_url=url,
            request_params={"date": date_range, "format": format},
            response_metadata={
                "content_type": response.headers.get("Content-Type", ""),
                "status_code": response.status_code,
            },
            payload_format=format,
            source_publication_timestamp=dt.datetime.now(tz=dt.UTC),
            source_version=response.headers.get("ETag"),
        )

    @staticmethod
    def parse(payload: bytes) -> list[dict[str, Any]]:
        """Parse the World Bank JSON envelope into a list of records.

        Returns an empty list if the second envelope element is not a list
        (e.g. when the source returns only metadata).
        """

        import json

        envelope = json.loads(payload)
        if not isinstance(envelope, list) or len(envelope) < 2:
            return []
        records = envelope[1]
        if not isinstance(records, list):
            return []
        return [dict(r) for r in records]
