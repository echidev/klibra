"""Integration contract for the in-memory Raw -> Bronze -> Silver -> Gold path."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from ingestion.connectors.base import ExtractionResult, SourceMetadata
from ingestion.storage.raw import RawStorageWriter
from orchestration.tasks import (
    apply_quality_gate,
    build_bronze,
    build_gold,
    build_silver,
    publish_gold,
    run_extraction,
    run_silver_tests,
    validate_raw,
)

PAYLOAD = (
    b'[{"page":1},[{"indicator":{"id":"NY.GDP.MKTP.KD.ZG",'
    b'"value":"GDP growth"},"country":{"id":"US",'
    b'"value":"United States"},"countryiso3code":"USA",'
    b'"date":"2023","value":2.5,"unit":"percent","decimal":1}]]'
)


class FakeConnector:
    run_id = "integration-run"

    def extract(self) -> ExtractionResult:
        return ExtractionResult(payload=PAYLOAD, source_url="https://example.test")

    def validate_response(self, payload: bytes) -> None:
        assert payload == PAYLOAD

    def emit_metadata(self, result: ExtractionResult) -> SourceMetadata:
        return SourceMetadata(
            source_id="worldbank",
            dataset_id="NY.GDP.MKTP.KD.ZG",
            retrieval_timestamp=datetime.now(UTC),
            source_url=result.source_url,
            request_params={},
            response_metadata={},
            content_hash=hashlib.sha256(PAYLOAD).hexdigest(),
            payload_format="json",
            run_id=self.run_id,
            connector_version="test",
        )


def test_raw_to_gold_pipeline() -> None:
    extracted = run_extraction(
        {"datasets": [{"source_id": "worldbank", "dataset_id": "NY.GDP.MKTP.KD.ZG"}]},
        connector_factory=lambda _definition: FakeConnector(),
    )
    raw_validated = validate_raw(extracted)
    bronze = build_bronze(raw_validated)
    quality = apply_quality_gate(bronze)
    silver = run_silver_tests(build_silver(quality))
    gold = publish_gold(build_gold(silver))

    assert gold["status"] == "PUBLISHED"
    assert gold["records_written"] == 1
    assert gold["records"][0]["metric_id"] == "gdp_growth_rate"
    assert gold["records"][0]["lineage_ref"].startswith("silver.")


def test_raw_writer_rejects_existing_objects() -> None:
    class Client:
        def __init__(self) -> None:
            self.objects: set[str] = set()

        def put_object(self, bucket_name, object_name, data, content_type=None):
            if object_name in self.objects:
                raise AssertionError("writer should check before put")
            self.objects.add(object_name)

        def stat_object(self, bucket_name, object_name):
            if object_name not in self.objects:
                raise FileNotFoundError(object_name)
            return object_name

    client = Client()
    writer = RawStorageWriter("test")
    writer.write_raw(client, "worldbank", "gdp", "run-1", b"payload", b"{}")
    try:
        writer.write_raw(client, "worldbank", "gdp", "run-1", b"payload", b"{}")
    except RuntimeError as exc:
        assert "raw write failed" in str(exc)
    else:
        raise AssertionError("duplicate raw object was accepted")
