"""Coverage tests for raw storage writer and bronze parser."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from ingestion.storage.raw import (
    LocalStorageWriter,
    RawStorageWriter,
)
from transformation.bronze.worldbank_indicators import build_bronze_records


def test_raw_storage_writer_prefixed_key() -> None:
    writer = RawStorageWriter("bucket", bucket_prefix="prefix")
    assert writer._prefixed_key("foo") == "prefix/foo"
    plain = RawStorageWriter("bucket")
    assert plain._prefixed_key("foo") == "foo"


def test_raw_storage_writer_write_raw_success() -> None:
    writer = RawStorageWriter("bucket")

    class FakeClient:
        def __init__(self):
            self.written: list[dict[str, Any]] = []

        def put_object(self, bucket, key, data, content_type=None):
            self.written.append({"bucket": bucket, "key": key, "data": data, "ct": content_type})

    client = FakeClient()
    key = writer.write_raw(
        client,
        "source",
        "dataset",
        "run",
        b"payload",
        b'{"manifest": true}',
    )
    assert "raw/source=source" in key
    assert "run_id=run/payload" in key
    assert len(client.written) == 2


def test_raw_storage_writer_write_raw_failure() -> None:
    writer = RawStorageWriter("bucket")

    class BrokenClient:
        def put_object(self, *args, **kwargs):
            raise OSError("boom")

    with pytest.raises(RuntimeError):
        writer.write_raw(BrokenClient(), "s", "d", "r", b"p", b"m")


def test_local_storage_writer_get_client_no_minio() -> None:
    writer = LocalStorageWriter("bucket")
    # When minio is importable it returns a client; otherwise RuntimeError
    try:
        client = writer.get_client()
        assert client is not None
    except RuntimeError:
        # minio not available in test env
        pass


def test_bronze_build_records_happy_path() -> None:
    envelope = b'[{"page": 1, "per_page": 50, "total": 1}, [{"indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"}, "country": {"id": "USA", "value": "United States"}, "countryiso3code": "USA", "date": "2024", "value": 123.45, "unit": "", "obs_status": "", "decimal": "1"}]]'
    records = build_bronze_records(
        source_id="worldbank",
        dataset_id="NY.GDP.MKTP.CD",
        raw_payload=envelope,
        ingestion_run_id="run1",
        ingestion_timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        raw_source_url="https://example.test",
    )
    assert len(records) == 1
    assert records[0]["country_id"] == "USA"
    assert records[0]["indicator_id"] == "NY.GDP.MKTP.CD"
    assert records[0]["value"] == 123.45
    assert records[0]["payload_hash"]


def test_bronze_build_records_invalid_json() -> None:
    records = build_bronze_records(
        source_id="worldbank",
        dataset_id="d",
        raw_payload=b"not json",
        ingestion_run_id="r",
        ingestion_timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        raw_source_url="u",
    )
    assert records == []


def test_bronze_build_records_short_envelope() -> None:
    records = build_bronze_records(
        source_id="worldbank",
        dataset_id="d",
        raw_payload=b"[1]",
        ingestion_run_id="r",
        ingestion_timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        raw_source_url="u",
    )
    assert records == []


def test_bronze_build_records_null_value() -> None:
    envelope = b'[{"page": 1}, [{"indicator": {"id": "X", "value": "X"}, "country": {"id": "USA", "value": "U"}, "countryiso3code": "USA", "date": "2024", "value": null, "unit": "", "obs_status": "", "decimal": "0"}]]'
    records = build_bronze_records(
        source_id="worldbank",
        dataset_id="X",
        raw_payload=envelope,
        ingestion_run_id="r",
        ingestion_timestamp=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        raw_source_url="u",
    )
    assert records[0]["value"] is None
