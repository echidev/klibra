"""Unit tests for the ECB SDMX connector.

Covers FR-1..FR-10 of spec.md §002-A and SC-A-1..SC-A-5.
"""

from __future__ import annotations

from unittest.mock import patch

from ingestion.connectors.base import ExtractionResult, HttpResponse
from ingestion.connectors.ecb import EcbSdmxConnector
from ingestion.util.idempotency import compute_idempotency_key

ECB_CSV = b"""KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,OBS_STATUS,OBS_CONF,OBS_PRE_BREAK,OBS_COM,TIME_FORMAT,BREAKS,COLLECTION,COMPILING_ORG,DISS_ORG,DOM_SER_IDS,PUBL_ECB,PUBL_MU,PUBL_PUBLIC,UNIT_INDEX_BASE,COMPILATION,COVERAGE,DECIMALS,NAT_TITLE,SOURCE_AGENCY,SOURCE_PUB,TITLE,TITLE_COMPL,UNIT,UNIT_MULT
EXR.A.USD.EUR.SP00.A,A,USD,EUR,SP00,A,2025,1.081268627451,A,F,,,P1Y,,A,,,,,,,,,,4,,4F0,,US dollar/Euro ECB reference exchange rate,2025,USD,0
EXR.A.USD.EUR.SP00.A,A,USD,EUR,SP00,A,2024,1.08238046875,A,F,,,P1Y,,A,,,,,,,,,,4,,4F0,,US dollar/Euro ECB reference exchange rate,2024,USD,0
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-09-04,1.16,A,F,,,P1D,,A,,,,,,,,,,4,,4F0,,US dollar/Euro ECB reference exchange rate,2026-09-04,USD,0
EXR.M.USD.EUR.SP00.A,M,USD,EUR,SP00,A,2026-08,1.158,A,F,,,P1M,,A,,,,,,,,,,4,,4F0,,US dollar/Euro ECB reference exchange rate,2026-08,USD,0
"""


def _csv_response(url: str, payload: bytes = ECB_CSV) -> HttpResponse:
    return HttpResponse(
        status_code=200,
        headers={"Content-Type": "text/csv", "ETag": 'W/"abc"'},
        body=payload,
        url=url,
    )


def test_ecb_connector_explicit_frequency() -> None:
    c = EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A")
    r = c.extract(last_n_observations=4)
    assert isinstance(r, ExtractionResult)
    assert r.response_metadata["status_code"] == 200
    assert r.payload_format == "csvdata"
    assert r.source_url.startswith(
        "https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A"
    )
    # last_n_observations passed through
    assert r.request_params.get("lastNObservations") == "4"
    # Content-Type captured
    assert "text/csv" in r.response_metadata["content_type"]


def test_ecb_connector_wildcard_frequency() -> None:
    c = EcbSdmxConnector(dataset_id="EXR..USD.EUR.SP00.A")
    # Mock send_request to return a sample CSV for the wildcard path
    sample_csv = (
        b"KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,"
        b"OBS_STATUS,OBS_CONF,OBS_PRE_BREAK,OBS_COM,TIME_FORMAT,BREAKS,COLLECTION,"
        b"COMPILING_ORG,DISS_ORG,DOM_SER_IDS,PUBL_ECB,PUBL_MU,PUBL_PUBLIC,"
        b"UNIT_INDEX_BASE,COMPILATION,COVERAGE,DECIMALS,NAT_TITLE,SOURCE_AGENCY,"
        b"SOURCE_PUB,TITLE,TITLE_COMPL,UNIT,UNIT_MULT\n"
        b"EXR..USD.EUR.SP00.A,,USD,EUR,SP00,A,2026-01-01,1.15,A,F,,,P1D,,A,,,,,,,99Q1=100,,,4,,4F0,,US dollar/Euro,2026-01-01,USD,0\n"
    )
    from ingestion.connectors import ecb as ecb_mod

    resp = HttpResponse(
        status_code=200,
        headers={"Content-Type": "text/csv"},
        body=sample_csv,
        url="https://data-api.ecb.europa.eu/service/data/EXR/?.USD.EUR.SP00.A?format=csvdata",
    )
    with patch.object(ecb_mod, "send_request", return_value=resp):
        r = c.extract(last_n_observations=1)
    assert "EXR" in r.source_url
    assert "USD.EUR.SP00.A" in r.source_url
    assert len(r.payload) > 0


def test_ecb_connector_split_dataset_id() -> None:
    flow, key = EcbSdmxConnector._split_dataset_id("EXR.M.USD.EUR.SP00.A")
    assert flow == "EXR"
    assert key == "M.USD.EUR.SP00.A"

    flow2, key2 = EcbSdmxConnector._split_dataset_id("EXR..USD.EUR.SP00.A")
    assert flow2 == "EXR"
    assert key2 == "?.USD.EUR.SP00.A"


def test_ecb_connector_frequency_hint() -> None:
    assert EcbSdmxConnector._frequency_hint("EXR.M.USD.EUR.SP00.A") == "M"
    assert EcbSdmxConnector._frequency_hint("EXR..USD.EUR.SP00.A") == "?"
    assert EcbSdmxConnector._frequency_hint("EXR") == "M"  # default


def test_ecb_connector_parses_csv_to_bronze() -> None:
    records = EcbSdmxConnector.parse_bronze(ECB_CSV, "EXR.M.USD.EUR.SP00.A")
    assert len(records) == 4
    # daily and monthly entries co-exist; the parser preserves frequency
    frequencies = {r["frequency"] for r in records}
    assert frequencies == {"A", "D", "M"}
    # all values parsed as floats
    assert all(isinstance(r["value"], float) for r in records)


def test_ecb_connector_retry_on_429() -> None:
    """429 triggers backoff + retry; eventually 200 returns response.

    We mock ``requests.request`` (the layer below ``base.send_request``)
    so the real retry logic in ``base.send_request`` is exercised.
    """

    c = EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A")

    class _Resp:
        def __init__(self, status_code, headers, text="", content=b"hello"):
            self.status_code = status_code
            self.headers = headers
            self.content = content
            self.text = text
            self.reason = "Too Many Requests" if status_code == 429 else "OK"
            self.url = "https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A"

        def raise_for_status(self):
            import requests as _r

            if self.status_code >= 400:
                raise _r.exceptions.HTTPError(f"{self.status_code} Error", response=self)

    # First call returns 429, second call returns 200
    responses = iter(
        [
            _Resp(429, {"Retry-After": "0"}, text="Too Many Requests", content=b""),
            _Resp(
                200,
                {"Content-Type": "text/csv", "ETag": 'W/"abc"'},
                text="header\nrow",
                content=ECB_CSV,
            ),
        ]
    )

    def fake_request(*_args, **_kwargs):
        r = next(responses)
        if r.status_code == 429:
            raise __import__("requests").exceptions.HTTPError("429 Too Many Requests", response=r)
        return r

    with (
        patch("requests.request", side_effect=fake_request),
        patch("ingestion.connectors.base.time.sleep", return_value=None),
    ):
        r = c.extract(last_n_observations=1)
    assert r.response_metadata["status_code"] == 200
    assert len(r.payload) > 0


def test_ecb_connector_idempotency_key_deterministic() -> None:
    """Same inputs produce the same idempotency key (TDD §71)."""

    k1 = compute_idempotency_key("ecb", "EXR.M.USD.EUR.SP00.A", "2025", None, "abc123")
    k2 = compute_idempotency_key("ecb", "EXR.M.USD.EUR.SP00.A", "2025", None, "abc123")
    assert k1 == k2
    assert len(k1) == 64  # sha256 hex
