"""Shared SDMX helpers for ECM/BMD/I MF SDMX 2.1 REST endpoints — PRD §10.1, TDD §60.

ECB, IMF, and similar SDMX 2.1 providers share the same resource model:

  /service/data/{flowRef}/{key}?{query}
  /service/dataflow/{agencyID}/{id}/{version}

This module also handles the Accept-header / content-type negotiation that
each SDMX provider requires differently (Starbucks: CSV vs JSON).

Provides:
- ``build_sdmx_data_request``  — builds an ``HttpRequest`` for the data endpoint.
- ``build_sdmx_dataflow_request`` — builds a request for the dataflow discovery endpoint.
- ``accept_header_for_format`` — maps ``format=csvdata`` to the correct Accept header.

Usage (ECB):

    from ingestion.connectors.sdmx import build_sdmx_data_request

    req = build_sdmx_data_request(
        base_url="https://data-api.ecb.europa.eu/service",
        flow_ref="EXR",
        key="M.USD.EUR.SP00.A",
        params={"lastNObservations": "24", "format": "csvdata"},
    )
    response = send_request(req)

Implements work on top of ``ingestion.connectors.base.send_request`` and
do NOT read env / secrets directly.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from ingestion.connectors.base import (
    REQUEST_TIMEOUT_SECONDS,
    HttpRequest,
)

__all__ = [
    "accept_header_for_format",
    "build_sdmx_data_request",
    "build_sdmx_dataflow_request",
]

# Mapping from KLIBRA ``format=`` param to SDMX content negotiation.
_ACCEPT_BY_FORMAT: dict[str, str] = {
    "csvdata": "text/csv",
    "json": "application/vnd.sdmx.data+json; version=2.0.0",
    "sdmx-json": "application/vnd.sdmx.data+json; version=2.0.0",
    "sdmx-xml": "application/vnd.sdmx.structurespecific+xml; version=2.1.0",
    "csv": "text/csv",
}


def accept_header_for_format(fmt: str) -> str:
    """Return the SDMX Accept header for ``fmt`` (csvdata, json, sdmx-xml)."""

    return _ACCEPT_BY_FORMAT.get(fmt.lower(), "application/octet-stream")


def build_sdmx_data_request(
    *,
    base_url: str,
    flow_ref: str,
    key: str | None = None,
    params: dict[str, Any] | None = None,
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
) -> HttpRequest:
    """Build an ``HttpRequest`` for the SDMX ``/service/data/`` endpoint."""

    base_url = base_url.rstrip("/")
    fmt = (params or {}).get("format", "csvdata")
    accept = accept_header_for_format(fmt)
    # Build the path: /service/data/{flowRef}/{key}
    path = f"/data/{urllib.parse.quote(flow_ref)}"
    if key:
        path += f"/{urllib.parse.quote(key, safe='.;+=,?')}"
    url = f"{base_url}{path}"
    headers = {"Accept": accept}
    return HttpRequest(
        method="GET",
        url=url,
        headers=headers,
        params=dict(params or {}),
        timeout_seconds=timeout_seconds,
    )


def build_sdmx_dataflow_request(
    *,
    base_url: str,
    agency_id: str = "ECB",
    flow_id: str = "EXR",
    version: str | None = None,
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
) -> HttpRequest:
    """Build an ``HttpRequest`` for the SDMX ``/service/dataflow/`` endpoint.

    Used to verify a dataflow exists and to capture its ``urn``.
    """

    base_url = base_url.rstrip("/")
    path = f"/dataflow/{urllib.parse.quote(agency_id)}/{urllib.parse.quote(flow_id)}"
    if version:
        path += f"/{urllib.parse.quote(version)}"
    return HttpRequest(
        method="GET",
        url=f"{base_url}{path}",
        headers={"Accept": "application/vnd.sdmx.structure+xml; version=2.1.0"},
        params={"detail": "allstubs"},
        timeout_seconds=timeout_seconds,
    )
