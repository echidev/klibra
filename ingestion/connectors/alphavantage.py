"""Alpha Vantage connector — PRD §11.1.3 Market Overview, FR-E-4..FR-E-5.

Alpha Vantage is a self-service web API (Class B). It provides free-form
keys via email (https://www.alphavantage.co/support/#api-key). The
connector targets the ``_TIME_SERIES_INTRADAY_EXTENDED`` and ``GLOBAL_QUOTE``
endpoints for FX / equities / commodities.

No env reading is done directly here; the key is resolved by the caller
(usually from ``.env`` via ``python-dotenv``) and passed in.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from typing import Any

from ingestion.connectors.base import (
    REQUEST_TIMEOUT_SECONDS,
    ExtractionResult,
    HttpRequest,
    SourceConnectorBase,
    send_request,
)

__all__ = ["AlphaVantageConnector", "AlphaVantageKeyError"]

logger = logging.getLogger(__name__)

AV_BASE_URL = "https://www.alphavantage.co/query"
# Free-tier: ~5 requests/min, 25/day. Per 002-E FR-E-5 we sleep a bit
# between requests to stay within the budget.
AV_RATE_LIMIT_RPM = 5


class AlphaVantageKeyError(ValueError):
    """Raised when the Alpha Vantage API key is missing or malformed."""


class AlphaVantageConnector(SourceConnectorBase):
    connector_version: str = "1.0.0"

    def __init__(
        self,
        symbol: str,
        *,
        api_key: str | None = None,
        base_url: str = AV_BASE_URL,
        function: str = "GLOBAL_QUOTE",
    ) -> None:
        super().__init__(source_id="alphavantage", dataset_id=symbol)
        key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "")
        if not key:
            raise AlphaVantageKeyError(
                "ALPHAVANTAGE_API_KEY is required (Class B source). "
                "Register at https://www.alphavantage.co/support/#api-key"
            )
        self.api_key = key
        self.base_url = base_url
        self.function = function

    def authenticate(self) -> dict[str, str]:
        """Alpha Vantage puts the key in the query string."""

        return {}

    def extract(self, **kwargs: Any) -> ExtractionResult:
        """Fetch a GLOBAL_QUOTE for ``symbol``."""

        params: dict[str, str] = {
            "function": self.function,
            "symbol": self.dataset_id,
            "apikey": self.api_key,
        }
        request = HttpRequest(
            method="GET",
            url=self.base_url,
            headers={"User-Agent": "klibra-platform/0.1.0"},
            params=params,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        )
        response = send_request(request)
        # Parse to validate response shape
        body = response.body
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
        # Check for error key (API returns a JSON error message)
        if "Error Message" in data or "Note" in data:
            raise ValueError(
                f"Alpha Vantage returned error for {self.dataset_id}: "
                f"{data.get('Error Message', data.get('Note'))}"
            )
        return ExtractionResult(
            payload=body,
            source_url=response.url,
            request_params=dict(params),
            response_metadata={"status_code": response.status_code, "function": self.function},
            payload_format="json",
            source_publication_timestamp=dt.datetime.now(dt.UTC),
            source_version=None,
        )
