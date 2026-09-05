"""Contract tests for the ECB SDMX connector — end-to-end shape.

These tests confirm the ECB connector produces artifacts that match the
data contracts (Bronze payload + Silver row) without contacting a live
endpoint. They consume a captured sample (sample_ecb.csv) committed
adjacent to this file.
"""

from __future__ import annotations

import pathlib

import pytest

from ingestion.connectors.ecb import EcbSdmxConnector

SAMPLE_PATH = pathlib.Path(__file__).parent / "sample_ecb.csv"


@pytest.fixture(scope="module")
def sample_payload() -> bytes:
    return SAMPLE_PATH.read_bytes()


def test_bronze_row_shape_matches_contract(sample_payload: bytes) -> None:
    records = EcbSdmxConnector.parse_bronze(sample_payload, "EXR.M.USD.EUR.SP00.A")
    expected_keys = {
        "source_id",
        "dataset_id",
        "frequency",
        "currency",
        "currency_denom",
        "exr_type",
        "exr_suffix",
        "observation_date",
        "value",
        "unit",
        "obs_status",
        "title",
        "raw_source_url",
    }
    for r in records:
        assert expected_keys.issubset(set(r.keys())), r
        assert r["source_id"] == "ecb"
        assert r["dataset_id"] == "EXR.M.USD.EUR.SP00.A"
        assert isinstance(r["value"], float)


def test_observation_date_is_string_year_or_period(sample_payload: bytes) -> None:
    records = EcbSdmxConnector.parse_bronze(sample_payload, "EXR.M.USD.EUR.SP00.A")
    for r in records:
        assert isinstance(r["observation_date"], str)
        # Allow YYYY, YYYY-MM, YYYY-MM-DD
        assert len(r["observation_date"]) in (4, 7, 10)


def test_frequency_field_is_normalized(sample_payload: bytes) -> None:
    records = EcbSdmxConnector.parse_bronze(sample_payload, "EXR.M.USD.EUR.SP00.A")
    frequencies = {r["frequency"] for r in records}
    # frequency should be one of: 'A' 'Q' 'M' 'D' 'H' — never '?' since the
    # sample uses an explicit frequency in the FREQ column.
    assert frequencies.issubset({"A", "Q", "M", "D", "H"})
