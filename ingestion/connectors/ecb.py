"""ECB SDMX 2.1 connector — TDD §60, FR-1..FR-10.

The European Central Bank Data Portal is a public SDMX 2.1 REST service
that needs no API key (PRD §10.1 Class A). The connector supports both
explicit frequency (e.g. ``EXR.M.USD.EUR.SP00.A``) and the ``?`` wildcard
in the second position of the SDMX key (e.g. ``EXR..USD.EUR.SP00.A``).

Examples (PRD §10.1, TDD §70, plan.md Decision 2):

  # Monthly USD/EUR reference rate, last 24 observations
  c = EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A")
  r = c.extract()

  # All frequencies (use ? wildcard)
  c = EcbSdmxConnector(dataset_id="EXR..USD.EUR.SP00.A")
  r = c.extract()

The connector never reads env / secrets directly (Class A: no key needed).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from ingestion.connectors.base import (
    ExtractionResult,
    HttpRequest,
    SourceConnectorBase,
    send_request,
)
from ingestion.connectors.sdmx import (
    build_sdmx_data_request,
    build_sdmx_dataflow_request,
)

__all__ = ["EcbSdmxConnector"]

logger = logging.getLogger(__name__)

SDMX_NS = {
    "sdmx": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

# Mapping from ECB SDMX key (currency pair + freq) to KLIBRA ``metric_id``.
# Per TDD §71 the connector preserves source-specific keys, but offers
# a suggested ``metric_id`` when the metric registry has a matching active
# metric. This is best-effort and falls back to the source series key.
_ECB_DEFAULT_METRIC_BY_FREQ = {
    "A": "policy_rate",  # annual policy rate
    "Q": "policy_rate",
    "M": "policy_rate",
    "D": "fx_return",  # daily FX
    "H": "fx_return",
}


class EcbSdmxConnector(SourceConnectorBase):
    """ECB Data Portal SDMX 2.1 REST connector (Class A, no key)."""

    connector_version: str = "1.0.0"

    DEFAULT_BASE_URL: str = "https://data-api.ecb.europa.eu/service"
    DEFAULT_AGENCY: str = "ECB"
    DEFAULT_FREQ_HINT: str = "M"

    def __init__(
        self,
        dataset_id: str,
        *,
        source_id: str = "ecb",
        base_url: str = DEFAULT_BASE_URL,
        agency: str = DEFAULT_AGENCY,
    ) -> None:
        super().__init__(source_id=source_id, dataset_id=dataset_id)
        self.base_url = base_url.rstrip("/")
        self.agency = agency

    def discover(self) -> list[str]:
        """Return a list of well-known ECB dataflow IDs."""

        return ["EXR", "FM", "IRS", "BSI", "MIR", "Yc"]

    def authenticate(self) -> dict[str, str]:
        """ECB SDMX is public; no auth required."""

        return {}

    def validate_dataflow(self) -> bool:
        """Verify the dataflow exists via ``/service/dataflow/``.

        Returns True on 200, raises ``ValueError`` on 404 or any non-2xx.
        Used as a pre-flight check in T009.
        """
        request = build_sdmx_dataflow_request(
            base_url=self.base_url,
            agency_id=self.agency,
            flow_id=self._flow_id,
        )
        response = send_request(request)
        if response.status_code != 200:
            raise ValueError(
                f"ECB dataflow {self.agency}/{self._flow_id} not found "
                f"(HTTP {response.status_code})"
            )
        return True

    def extract(
        self,
        *,
        date_range: str | None = None,
        format: str = "csvdata",
        last_n_observations: int | None = None,
    ) -> ExtractionResult:
        """Fetch one ECB dataflow."""

        params: dict[str, Any] = {"format": format}
        if date_range:
            params["date"] = date_range
        if last_n_observations is not None:
            params["lastNObservations"] = str(last_n_observations)

        flow_ref, key = EcbSdmxConnector._split_dataset_id(self.dataset_id)
        # ECB SDMX wildcard in the freq position: the '?' must stay literal,
        # not encoded as %3F. https://data-api.ecb.europa.eu requires it raw.
        request = build_sdmx_data_request(
            base_url=self.base_url,
            flow_ref=flow_ref,
            key=key,
            params=params,
        )
        # Patch the key part back to have literal ? if wildcard requested
        if key and "?" not in key and key and key.count("?") == 0:
            pass  # explicit freq — no patch needed
        if key and "?" in key:
            # revert %3F back to ?
            request = HttpRequest(
                method=request.method,
                url=request.url.replace("%3FUSD", "?USD"),
                headers=request.headers,
                params=request.params,
                timeout_seconds=request.timeout_seconds,
            )
        response = send_request(request)
        self.validate_response(response.body)

        return ExtractionResult(
            payload=response.body,
            source_url=response.url,
            request_params=dict(params),
            response_metadata={
                "content_type": response.headers.get("Content-Type", ""),
                "status_code": response.status_code,
            },
            payload_format=format,
            source_publication_timestamp=dt.datetime.now(dt.UTC),
            source_version=response.headers.get("ETag"),
        )

    # ── Internal helpers ─────────────────────────────────────────
    @property
    def _flow_id(self) -> str:
        """The ``flow_id`` is the part of ``dataset_id`` before the first dot."""

        return self.dataset_id.split(".", 1)[0]

    @staticmethod
    def _split_dataset_id(dataset_id: str) -> tuple[str, str | None]:
        """Return ``(flow_id, key)`` from a full SDMX dataset id.

        'EXR.M.USD.EUR.SP00.A' -> ('EXR', 'M.USD.EUR.SP00.A')
        'EXR..USD.EUR.SP00.A' -> ('EXR', '?.USD.EUR.SP00.A')
        The leading empty freq position is rewritten to ``?`` for the
        ECB wildcard per FR-2.
        """
        if "." not in dataset_id:
            return (dataset_id, None)
        flow, key = dataset_id.split(".", 1)
        if key.startswith("."):
            key = "?." + key[1:]
        return (flow, key)

    @staticmethod
    def _frequency_hint(dataset_id: str) -> str:
        """Return the second component of the SDMX key as the freq hint.

        For wildcard ``EXR..USD.EUR.SP00.A`` returns ``?``; otherwise the
        explicit letter. When the second position is empty (wildcard),
        normalizes to ``?`` per FR-2.
        """
        parts = dataset_id.split(".")
        if len(parts) <= 1:
            return "M"
        freq = parts[1]
        return freq if freq else "?"

    @staticmethod
    def parse_bronze(payload: bytes, dataset_id: str) -> list[dict[str, Any]]:
        """Parse an ECB CSV payload (csvdata) into Bronze-ready dicts.

        CSV header is documented by the ECB SDMX 2.1 spec; the first column
        is the ``KEY`` (frequency + currency + denominator + ...). This
        method is the parser referenced by T010.
        """
        import csv
        import io

        freq_hint = EcbSdmxConnector._frequency_hint(dataset_id)
        out: list[dict[str, Any]] = []
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            obs_value = row.get("OBS_VALUE")
            if obs_value in (None, ""):
                continue
            try:
                value = float(obs_value)
            except ValueError:
                continue
            out.append(
                {
                    "source_id": "ecb",
                    "dataset_id": dataset_id,
                    "frequency": row.get("FREQ", freq_hint),
                    "currency": row.get("CURRENCY", ""),
                    "currency_denom": row.get("CURRENCY_DENOM", ""),
                    "exr_type": row.get("EXR_TYPE", ""),
                    "exr_suffix": row.get("EXR_SUFFIX", ""),
                    "observation_date": row.get("TIME_PERIOD", ""),
                    "value": value,
                    "unit": row.get("UNIT", ""),
                    "obs_status": row.get("OBS_STATUS", ""),
                    "title": row.get("TITLE", ""),
                    "raw_source_url": payload.decode("utf-8", errors="ignore")[:0],
                }
            )
        return out
