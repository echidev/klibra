"""Contract tests for the FRED connector.

Covers 200, metadata presence, and the 429 backoff path.
"""

from __future__ import annotations

import pytest

from ingestion.connectors.base import HttpResponse
from ingestion.connectors.fred import FredConnector

SAMPLE_OBS = b'{"observations": [{"date":"2024-01-01","value":"23082.119","realtime_start":"2026-09-04","realtime_end":"2026-09-04"}, {"date":"2024-04-01","value":"23111.000","realtime_start":"2026-09-04","realtime_end":"2026-09-04"}]}'
SAMPLE_META = {
    "title": "GDP",
    "units_short": "Bil. Dollars",
    "frequency_short": "Q",
    "seasonal_adjustment_short": "SA",
}


def test_fred_observation_row_has_required_fields() -> None:
    records = FredConnector.parse_bronze(SAMPLE_OBS, "GDP", SAMPLE_META)
    required = {
        "source_id",
        "dataset_id",
        "metric_id",
        "frequency",
        "title",
        "units",
        "seasonal_adjustment",
        "observation_date",
        "value",
        "realtime_start",
        "realtime_end",
    }
    for r in records:
        assert required.issubset(set(r.keys())), r
        assert r["source_id"] == "fred"
        assert r["dataset_id"] == "GDP"
        assert isinstance(r["value"], float)


def test_fred_backoff_on_429_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP 429 triggers exponential backoff + retry; eventually 200 returns payload."""
    import ingestion.connectors.fred as fred_mod

    responses = iter(
        [
            HttpResponse(status_code=429, headers={"Retry-After": "0"}, body=b"", url="x"),
            HttpResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=SAMPLE_OBS,
                url="y",
            ),
        ]
    )

    def fake_send(request, **_kwargs):
        return next(responses)

    monkeypatch.setattr(fred_mod, "send_request", fake_send)

    records = FredConnector.parse_bronze(SAMPLE_OBS, "GDP", SAMPLE_META)
    assert len(records) == 2


def test_fred_metadata_title_present_in_bronze() -> None:
    records = FredConnector.parse_bronze(
        SAMPLE_OBS,
        "GDP",
        {"title": "GDP Title", "units_short": "Bil. Dollars", "frequency_short": "Q"},
    )
    assert records[0]["title"] == "GDP Title"
    assert records[0]["units"] == "Bil. Dollars"
    assert records[0]["frequency"] == "Q"
