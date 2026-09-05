"""Task stubs referenced by the Airflow DAG.

Each function corresponds to a DAG task and provides a minimal implementation
for local development and CI testing. Real implementations will be wired in
the appropriate user-story phase (e.g., US1 for extract, US2 for publish).
"""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ingestion.connectors.alphavantage import AlphaVantageConnector
from ingestion.connectors.fred import FredConnector
from ingestion.connectors.ecb import EcbSdmxConnector
# existing imports ...
from ingestion.storage.raw import ObjectClient, RawStorageWriter
from ingestion.util.logging import log_event
from ingestion.util.manifest import build_manifest, manifest_to_json
from ingestion.util.metric_mapping import semantic_metric_id
from transformation.bronze.worldbank_indicators import build_bronze_records
from transformation.quality.framework import QualityFramework, QualityOutcome

ConnectorFactory = Callable[[dict[str, Any]], SourceConnectorBase]


def _default_connector(dataset: dict[str, Any]) -> SourceConnectorBase:
    source_id = dataset["source_id"]
    if source_id == "worldbank":
        return WorldBankConnector(dataset_id=dataset["dataset_id"])
    if source_id == "alphavantage":
        return AlphaVantageConnector(symbol=dataset["dataset_id"], api_key="${ALPHAVANTAGE_API_KEY}")
    if source_id == "fred":
        return FredConnector(series_id=dataset["dataset_id"], api_key="${FRED_API_KEY}")
    if source_id == "ecb":
        return EcbSdmxConnector(dataset_id=dataset["dataset_id"])
    raise ValueError(f"unsupported source connector: {source_id}")



def discover_datasets(catalog_path: str = "docs/data/source_catalog.yaml") -> dict[str, Any]:
    """Load enabled dataset definitions from the source catalog."""
    import yaml  # type: ignore[import-untyped]

    catalog = yaml.safe_load(Path(catalog_path).read_text())
    datasets: list[dict[str, Any]] = []
    for source_id, source in (catalog.get("sources") or {}).items():
        if source.get("live_request_verified") is False:
            continue
        if source_id == "worldbank":
            datasets.extend(
                {"source_id": source_id, "dataset_id": dataset_id}
                for dataset_id in WorldBankConnector().discover()
            )
    log_event(
        20, "datasets discovered", service="klibra-orchestration", details={"count": len(datasets)}
    )
    return {"datasets": datasets, "count": len(datasets)}


def run_extraction(
    dataset: dict[str, Any],
    *,
    connector_factory: ConnectorFactory | None = None,
    storage_writer: RawStorageWriter | None = None,
    storage_client: ObjectClient | None = None,
) -> dict[str, Any]:
    """Extract each discovered dataset and optionally persist Raw objects."""
    factory = connector_factory or _default_connector
    results: list[dict[str, Any]] = []
    for definition in dataset.get("datasets", [dataset]):
        connector = factory(definition)
        result = connector.extract()
        connector.validate_response(result.payload)
        metadata = connector.emit_metadata(result)
        item: dict[str, Any] = {
            "source_id": definition["source_id"],
            "dataset_id": definition["dataset_id"],
            "run_id": connector.run_id,
            "payload": result.payload,
            "source_url": result.source_url,
            "metadata": metadata,
            "result": result,
        }
        if storage_writer is not None and storage_client is not None:
            manifest = build_manifest(
                source_id=metadata.source_id,
                dataset_id=metadata.dataset_id,
                run_id=metadata.run_id,
                source_url=metadata.source_url,
                content_hash=metadata.content_hash,
                payload_format=metadata.payload_format,
                request_params=metadata.request_params,
                response_metadata=metadata.response_metadata,
                source_publication_timestamp=metadata.source_publication_timestamp,
                source_version=metadata.source_version,
                retrieved_at=metadata.retrieval_timestamp,
                connector_version=metadata.connector_version,
            )
            item["raw_key"] = storage_writer.write_raw(
                storage_client,
                metadata.source_id,
                metadata.dataset_id,
                metadata.run_id,
                result.payload,
                manifest_to_json(manifest).encode(),
            )
        results.append(item)
    return {"status": "EXTRACTED", "items": results, "count": len(results)}


def validate_raw(extraction: dict[str, Any]) -> dict[str, Any]:
    """Validate every extracted payload and its content hash."""
    validated: list[dict[str, Any]] = []
    for item in extraction.get("items", []):
        payload = item["payload"]
        if not payload:
            raise ValueError(f"empty raw payload for {item['dataset_id']}")
        metadata = item["metadata"]
        actual_hash = hashlib.sha256(item["result"].payload).hexdigest()
        if actual_hash != metadata.content_hash:
            raise ValueError(f"invalid payload hash for {item['dataset_id']}")
        validated.append(item)
    return {"status": "VALIDATED", "items": validated, "count": len(validated)}


def build_bronze(validation: dict[str, Any]) -> dict[str, Any]:
    """Parse validated source payloads into source-aligned Bronze records."""
    batches: list[dict[str, Any]] = []
    for item in validation["items"]:
        if item["source_id"] != "worldbank":
            raise ValueError(f"Bronze parser is not configured for {item['source_id']}")
        records = build_bronze_records(
            source_id=item["source_id"],
            dataset_id=item["dataset_id"],
            raw_payload=item["payload"],
            ingestion_run_id=item["run_id"],
            ingestion_timestamp=item["metadata"].retrieval_timestamp,
            raw_source_url=item["source_url"],
        )
        if not records:
            raise ValueError(f"Bronze parser produced no records for {item['dataset_id']}")
        batches.append({**item, "records": records})
    return {"status": "BRONZE_BUILT", "batches": batches}


def apply_quality_gate(bronze_batch: dict[str, Any]) -> dict[str, Any]:
    """Block malformed batches and retain accepted records for Silver."""
    framework = QualityFramework()
    accepted: list[dict[str, Any]] = []
    for batch in bronze_batch["batches"]:
        outcome = framework.evaluate_batch(
            payload_present=True, schema_valid=bool(batch["records"])
        )
        if outcome in (QualityOutcome.QUARANTINED, QualityOutcome.REJECTED):
            raise ValueError(f"quality gate failed for {batch['dataset_id']}: {outcome.value}")
        accepted.append(batch)
    return {"status": "QUALITY_ACCEPTED", "batches": accepted}


def build_silver(quality_passed: dict[str, Any]) -> dict[str, Any]:
    """Map accepted Bronze rows into the canonical Silver observation grain."""
    records = [
        _canonical_silver(record, batch)
        for batch in quality_passed["batches"]
        for record in batch["records"]
        if record.get("value") is not None
    ]
    return {"status": "SILVER_BUILT", "records": records}


def _canonical_silver(record: dict[str, Any], batch: dict[str, Any]) -> dict[str, Any]:
    observation_year = int(record["observation_date"])
    return {
        "observation_id": (
            f"{batch['run_id']}:{record['country_id']}:{record['indicator_id']}"
            f":{record['observation_date']}"
        ),
        "metric_id": semantic_metric_id(record["source_id"], record["indicator_id"]),
        "entity_id": record["country_id"],
        "geography_id": record["country_id"],
        "observation_date": dt.date(observation_year, 1, 1).isoformat(),
        "value": record["value"],
        "unit": record["unit"],
        "source_id": record["source_id"],
        "dataset_id": record["dataset_id"],
        "publication_date": None,
        "ingestion_timestamp": record["ingestion_timestamp"],
        "effective_from": record["ingestion_timestamp"],
        "effective_to": None,
        "source_version": None,
        "quality_status": "ACCEPTED",
        "run_id": batch["run_id"],
        "payload_hash": record["payload_hash"],
    }


def run_silver_tests(silver_batch: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic boundary checks for the in-memory Silver batch."""
    records = silver_batch["records"]
    if any(not record["observation_id"] for record in records):
        raise ValueError("Silver contains an empty observation_id")
    return {**silver_batch, "status": "SILVER_VALIDATED"}


def build_gold(silver_passed: dict[str, Any]) -> dict[str, Any]:
    """Publish accepted current Silver observations as the macro Gold product."""
    records = [
        {
            **record,
            "gold_from": record["effective_from"],
            "lineage_ref": f"silver.fact_economic_observation:{record['observation_id']}",
        }
        for record in silver_passed["records"]
        if record["effective_to"] is None
        and record["quality_status"] in {"ACCEPTED", "ACCEPTED_WARNING"}
    ]
    return {
        "status": "GOLD_BUILT",
        "records": records,
        "run_id": records[0]["run_id"] if records else "",
    }


def publish_gold(gold_batch: dict[str, Any]) -> dict[str, Any]:
    """Return a publish receipt after verifying the Gold batch is non-empty."""
    if not gold_batch["records"]:
        raise ValueError("cannot publish an empty Gold batch")
    return {**gold_batch, "status": "PUBLISHED", "records_written": len(gold_batch["records"])}


def notify_owners(publish_result: dict[str, Any]) -> None:
    """Emit a structured completion event for the owning services."""
    log_event(
        20,
        "pipeline completed",
        service="klibra-orchestration",
        details={
            "status": publish_result.get("status"),
            "records_written": publish_result.get("records_written", 0),
        },
    )
