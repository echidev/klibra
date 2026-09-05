"""FRED connector — TDD §60, FR-1..FR-10 (002-B).

FRED is a public API with self-service personal key (Class B). The
connector uses a two-call pattern (TDD §14 metadata, plan.md Decision 3):

  1. ``GET /fred/series/series?series_id=...``   — fetch metadata (title,
     units, frequency, observation_start/end, seasonal_adjustment).
  2. ``GET /fred/series/observations?series_id=...`` — fetch observations.

The two results are merged into Bronze records. The ``metric_id`` defaults
to the series_id; a mapping from the metric registry may override it
(FR-7). The FRED key is 32 lowercase alphanum characters; the connector
validates shape and fails fast on missing or malformed keys.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
from typing import Any

from ingestion.connectors.base import (
    REQUEST_TIMEOUT_SECONDS,
    ExtractionResult,
    HttpRequest,
    SourceConnectorBase,
    send_request,
)

__all__ = ["FredConnector"]

logger = logging.getLogger(__name__)

# 32 lowercase alphanum characters per FRED registration docs
_KEY_PATTERN = re.compile(r"^[a-z0-9]{32}$")
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_RATE_LIMIT_RPM = 120  # documented at https://fred.stlouisfed.org/docs/api/fred/

# Maps common FRED series to the registered KLIBRA ``metric_id`` when
# the metric registry is reachable. If a series is not in this map,
# the connector falls back to the raw series_id (FR-7).
_FRED_DEFAULT_METRIC_MAP: dict[str, str] = {
    "GDP": "gdp_growth_rate",
    "GDPC1": "gdp_growth_rate",
    "CPIAUCSL": "inflation_rate",
    "UNRATE": "unemployment_rate",
    "FEDFUNDS": "policy_rate",
    "DFF": "policy_rate",
    "DEXUSEU": "fx_return",
    "VIXCLS": "market_volatility",
}


class FredKeyError(ValueError):
    """Raised when the FRED API key is missing or malformed."""


class FredConnector(SourceConnectorBase):
    """FRED connector (Class B, self-service key)."""

    connector_version: str = "1.0.0"

    def __init__(
        self,
        series_id: str,
        *,
        source_id: str = "fred",
        api_key: str | None = None,
        base_url: str = FRED_BASE_URL,
    ) -> None:
        super().__init__(source_id=source_id, dataset_id=series_id)
        resolved_key = api_key or os.environ.get("FRED_API_KEY", "")
        if not resolved_key:
            raise FredKeyError(
                "FRED_API_KEY is required (Class B source). "
                "Register at https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        if not _KEY_PATTERN.match(resolved_key):
            raise FredKeyError("FRED_API_KEY must be 32 lowercase alphanum characters")
        self.api_key = resolved_key
        self.base_url = base_url.rstrip("/")

    def discover(self) -> list[str]:
        """Return well-known FRED series IDs (no live call)."""

        return list(_FRED_DEFAULT_METRIC_MAP.keys())

    def authenticate(self) -> dict[str, str]:
        """FRED passes the key as a query parameter, not a header."""

        return {}

    def _build_request(
        self,
        endpoint: str,
        extra_params: dict[str, Any] | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> HttpRequest:
        params = {"series_id": self.dataset_id, "api_key": self.api_key, "file_type": "json"}
        if extra_params:
            params.update(extra_params)
        return HttpRequest(
            method="GET",
            url=f"{self.base_url}{endpoint}",
            params=params,
            timeout_seconds=timeout,
        )

    def _fetch_metadata(self) -> dict[str, Any]:
        """Fetch FRED series metadata via ``/fred/series/``."""

        response = send_request(self._build_request("/series"))
        if response.status_code != 200:
            raise ValueError(
                f"FRED /series returned HTTP {response.status_code} for "
                f"series_id={self.dataset_id}"
            )
        import json

        body = json.loads(response.body)
        seriess = body.get("seriess") or []
        if not seriess:
            raise ValueError(f"FRED returned no series for series_id={self.dataset_id}")
        return dict(seriess[0])

    def _fetch_observations(
        self,
        *,
        observation_start: str | None = None,
        observation_end: str | None = None,
        realtime_start: str | None = None,
        realtime_end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch FRED observations via ``/fred/series/observations``."""

        params: dict[str, Any] = {}
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        if realtime_start:
            params["realtime_start"] = realtime_start
        if realtime_end:
            params["realtime_end"] = realtime_end

        response = send_request(self._build_request("/series/observations", params))
        if response.status_code != 200:
            raise ValueError(
                f"FRED /series/observations returned HTTP "
                f"{response.status_code} for series_id={self.dataset_id}"
            )
        import json

        body = json.loads(response.body)
        return list(body.get("observations") or [])

    def extract(self, **kwargs: Any) -> ExtractionResult:
        """Fetch metadata + observations and merge into a single payload.

        The payload is the raw ``/series/observations`` JSON. Bronze parsing
        (in T017) merges with the metadata file.
        """

        # We call both endpoints. Metadata first to fail fast on bad series_id.
        observation_start = kwargs.get("observation_start")
        observation_end = kwargs.get("observation_end")
        realtime_start = kwargs.get("realtime_start")
        realtime_end = kwargs.get("realtime_end")
        metadata = self._fetch_metadata()
        obs_payload = self._fetch_observations(
            observation_start=observation_start,
            observation_end=observation_end,
            realtime_start=realtime_start,
            realtime_end=realtime_end,
        )

        import json

        body = json.dumps({"metadata": metadata, "observations": obs_payload}).encode()
        url = (
            f"{self.base_url}/series/observations"
            f"?series_id={self.dataset_id}&api_key=***&file_type=json"
        )
        return ExtractionResult(
            payload=body,
            source_url=url,
            request_params={
                "observation_start": observation_start or "",
                "observation_end": observation_end or "",
            },
            response_metadata={
                "status_code": 200,
                "observation_count": str(len(obs_payload)),
                "title": str(metadata.get("title", "")),
                "frequency": str(metadata.get("frequency_short", "")),
            },
            payload_format="json",
            source_publication_timestamp=dt.datetime.now(dt.UTC),
            source_version=None,
        )

    @staticmethod
    def parse_bronze(
        payload: bytes, series_id: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Parse FRED observations payload and merge optional metadata."""

        import json

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []
        observations = data.get("observations") or []
        meta = metadata or {}
        out: list[dict[str, Any]] = []
        for o in observations:
            raw = o.get("value")
            if raw in (None, "."):
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            out.append(
                {
                    "source_id": "fred",
                    "dataset_id": series_id,
                    "metric_id": _FRED_DEFAULT_METRIC_MAP.get(series_id, series_id),
                    "frequency": meta.get("frequency_short", ""),
                    "title": meta.get("title", ""),
                    "units": meta.get("units_short", ""),
                    "seasonal_adjustment": meta.get("seasonal_adjustment_short", ""),
                    "observation_date": o.get("date", ""),
                    "value": value,
                    "realtime_start": o.get("realtime_start", ""),
                    "realtime_end": o.get("realtime_end", ""),
                }
            )
        return out
