"""Unit tests for the QuarantineStorageWriter (T026)."""

from __future__ import annotations

import json

from ingestion.storage.quarantine import (
    QuarantineStorageWriter,
    build_quarantine_manifest,
    quarantine_key,
)


class FakeClient:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, bucket_name, object_name, data, content_type=None):
        body = data.read() if hasattr(data, "read") else data
        self.objects[object_name] = body

    def stat_object(self, bucket_name, object_name):
        raise RuntimeError("not in CI scope")

    def head_object(self, **kwargs):
        raise FileNotFoundError("not in CI scope")


def test_quarantine_key_layout() -> None:
    key = quarantine_key("worldbank", "NY.GDP", "run-1", "obs-1")
    assert key == "quarantine/source=worldbank/dataset=NY.GDP/run_id=run-1/obs-1.json"


def test_build_quarantine_manifest_fields() -> None:
    rec = {
        "source_id": "worldbank",
        "dataset_id": "NY.GDP",
        "run_id": "run-1",
        "observation_id": "obs-1",
        "value": 1.2,
    }
    m = build_quarantine_manifest(rec, "missing_value")
    assert m["source_id"] == "worldbank"
    assert m["quality_status"] == "QUARANTINED"
    assert m["quarantine_reason"] == "missing_value"
    assert m["original_record"] == rec
    assert m["quarantine_timestamp"]


def test_write_quarantine_writes_to_bucket() -> None:
    client = FakeClient()
    w = QuarantineStorageWriter("klibra-data-quarantine")
    rec = {"source_id": "worldbank", "dataset_id": "NY.GDP", "observation_id": "obs-1"}
    key = w.write_quarantine(
        client, "worldbank", "NY.GDP", "run-1", rec, "missing_value", observation_id="obs-1"
    )
    assert key.endswith("obs-1.json")
    assert key in client.objects
    body = json.loads(client.objects[key])
    assert body["quarantine_reason"] == "missing_value"
    assert body["quality_status"] == "QUARANTINED"


def test_write_quarantine_swallows_adapter_errors() -> None:
    class Boom:
        def put_object(self, *a, **kw):
            raise RuntimeError("adapter down")

    w = QuarantineStorageWriter("klibra-data-quarantine")
    out = w.write_quarantine(
        Boom(), "worldbank", "NY.GDP", "run-1", {"observation_id": "x"}, "x", observation_id="x"
    )
    assert out == ""  # never raises; failure-isolated
