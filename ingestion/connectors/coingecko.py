"""CoinGecko connector — PRD §11.1.3 Market Overview, Class B.

Demo key via self-registration (no institutional proposal), sent as
``x-cg-demo-api-key`` header per https://docs.coingecko.com/reference/setting-up-demo-api-key.
The base URL supports both the public path and authenticated calls.
"""

from __future__ import annotations

import os
from typing import Any

from ingestion.connectors.base import (
    REQUEST_TIMEOUT_SECONDS,
    ExtractionResult,
    HttpRequest,
    SourceConnectorBase,
    send_request,
)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_DEMO_IDS = ("bitcoin", "ethereum", "tether")
__all__ = ["CoinGeckoConnector"]


class CoinGeckoConnector(SourceConnectorBase):
    """Class B connector for CoinGecko Demo API."""

    connector_version: str = "1.0.0"

    def __init__(
        self,
        coin_id: str = "bitcoin",
        *,
        api_key: str | None = None,
        base_url: str = COINGECKO_BASE_URL,
        dataset_id: str | None = None,
    ) -> None:
        resolved = dataset_id or coin_id
        super().__init__(source_id="coingecko", dataset_id=resolved)
        self.coin_id = coin_id
        self.api_key = api_key or os.environ.get("COINGECKO_DEMO_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        if self.api_key:
            return {"x-cg-demo-api-key": self.api_key}
        return {}

    def discover(self) -> list[str]:
        return [str(coin_id) for coin_id in COINGECKO_DEMO_IDS]

    def validate_access(self) -> None:
        return

    def authenticate(self) -> dict[str, Any]:
        return {}

    def _build_request(
        self,
        *,
        extra_params: dict[str, Any] | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> HttpRequest:
        params: dict[str, Any] = {"id": self.coin_id}
        if extra_params:
            params.update(extra_params)
        return HttpRequest(
            method="GET",
            url=f"{self.base_url}/simple/price",
            headers=self._headers(),
            params={
                "ids": self.coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            timeout_seconds=timeout,
        )

    def extract(self, **kwargs: Any) -> ExtractionResult:
        request = self._build_request()
        response = send_request(request)
        return ExtractionResult(
            payload=response.body,
            source_url=response.url,
            request_params=dict(request.params),
            response_metadata={"status_code": response.status_code},
            payload_format="json",
        )

    def validate_response(self, payload: bytes) -> None:
        import json

        body = json.loads(payload or b"{}")
        if not isinstance(body, dict) or not body:
            raise ValueError("CoinGecko payload is empty or invalid")

    def emit_metadata(self, result: ExtractionResult) -> Any:
        return super().emit_metadata(result)
