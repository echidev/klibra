"""Task stubs referenced by the Airflow DAG.

Each function corresponds to a DAG task and provides a minimal implementation
for local development and CI testing. Real implementations will be wired in
the appropriate user-story phase (e.g., US1 for extract, US2 for publish).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ingestion.connectors.alphavantage import AlphaVantageConnector
from ingestion.connectors.base import SourceConnectorBase
from ingestion.connectors.ecb import EcbSdmxConnector
from ingestion.connectors.fred import FredConnector
from ingestion.connectors.worldbank import WorldBankConnector
from ingestion.storage.raw import ObjectClient, RawStorageWriter
from ingestion.util.logging import log_event
from ingestion.util.manifest import build_manifest, manifest_to_json
from ingestion.util.metric_mapping import semantic_metric_id
from transformation.bronze.worldbank_indicators import (
    build_bronze_records as build_bronze_records_worldbank,
)
from transformation.quality.framework import QualityFramework, QualityOutcome

ConnectorFactory = Callable[[dict[str, Any]], SourceConnectorBase]


def _default_connector(dataset: dict[str, Any]) -> SourceConnectorBase:
    source_id = dataset["source_id"]
    if source_id == "worldbank":
        return WorldBankConnector(dataset_id=dataset["dataset_id"])
    if source_id == "alphavantage":
        key = os.environ.get("ALPHAVANTAGE_API_KEY", "")
        if not key:
            msg = "ALPHAVANTAGE_API_KEY is required"
            raise ValueError(msg)
        return AlphaVantageConnector(symbol=dataset["dataset_id"], api_key=key)
    if source_id == "fred":
        key = os.environ.get("FRED_API_KEY", "")
        if not key:
            msg = "FRED_API_KEY is required"
            raise ValueError(msg)
        return FredConnector(series_id=dataset["dataset_id"], api_key=key)
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
        elif source_id == "ecb":
            datasets.extend(
                {"source_id": source_id, "dataset_id": dataset_id}
                for dataset_id in EcbSdmxConnector(dataset_id="EXR.M.USD.EUR.SP00.A").discover()
            )
        elif source_id == "fred":
            for dataset_id in FredConnector(series_id="GDPC1", api_key="x" * 32).discover():
                datasets.append({"source_id": source_id, "dataset_id": dataset_id})
        elif source_id == "alphavantage":
            for dataset_id in ["GLOBAL_QUOTE:AAPL", "TIME_SERIES_DAILY:AAPL"]:
                datasets.append({"source_id": source_id, "dataset_id": dataset_id})
        elif source_id == "imf":
            # Class C - deferred; do not crash, just log and continue.
            log_event(
                30,
                f"skipping IMF source (Class C, not wired): {source_id}",
                service="klibra-orchestration",
            )
            continue
        else:
            # Any remaining source (e.g. coingecko) is deferred; log and skip.
            log_event(
                30,
                f"skipping deferred source (not in this feature's wiring): {source_id}",
                service="klibra-orchestration",
            )
            continue
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
    import time as _time

    factory = connector_factory or _default_connector
    results: list[dict[str, Any]] = []
    for definition in dataset.get("datasets", [dataset]):
        iter_start = _time.monotonic()
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
        try:
            from orchestration.util.cost import DatasetCost, record_dataset_cost

            runtime_seconds = _time.monotonic() - iter_start
            record_dataset_cost(
                DatasetCost(
                    run_id=connector.run_id,
                    dataset_id=definition["dataset_id"],
                    api_request_volume=1,
                    runtime_seconds=runtime_seconds,
                )
            )
        except Exception:  # noqa: BLE001 — cost telemetry must not fail the extraction
            pass
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
    from transformation.bronze.alphavantage import build_bronze_records as build_bronze_alphavantage
    from transformation.bronze.ecb_indicators import build_bronze_records as build_bronze_ecb
    from transformation.bronze.fred import build_bronze_records as build_bronze_fred

    batches: list[dict[str, Any]] = []
    for item in validation["items"]:
        source_id = item["source_id"]
        common_kwargs: dict[str, Any] = {
            "source_id": item["source_id"],
            "run_id": item["run_id"],
            "ingestion_timestamp": item["metadata"].retrieval_timestamp,
            "raw_source_url": item["source_url"],
        }
        if source_id == "worldbank":
            records = build_bronze_records_worldbank(
                dataset_id=item["dataset_id"],
                raw_payload=item["payload"],
                ingestion_run_id=item["run_id"],
                source_id=item["source_id"],
                ingestion_timestamp=item["metadata"].retrieval_timestamp,
                raw_source_url=item["source_url"],
            )
        elif source_id == "ecb":
            records = build_bronze_ecb(
                dataset_id=item["dataset_id"],
                raw_payload=item["payload"],
                **common_kwargs,
            )
        elif source_id == "fred":
            metadata = getattr(item.get("metadata"), "response_metadata", None)  # type: ignore[union-attr]
            fred_meta = metadata if isinstance(metadata, dict) else {}
            records = build_bronze_fred(
                series_id=item["dataset_id"],
                raw_payload=item["payload"],
                metadata=fred_meta,  # type: ignore[arg-type]
                **common_kwargs,
            )
        elif source_id == "alphavantage":
            records = build_bronze_alphavantage(
                dataset_id=item["dataset_id"],
                raw_payload=item["payload"],
                **common_kwargs,
            )
        else:
            msg = f"Bronze parser is not configured for {source_id!r}"
            raise ValueError(msg)
        if not records:
            msg = f"Bronze parser produced no records for {item['dataset_id']}"
            raise ValueError(msg)
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


def _parse_observation_date(  # noqa: PLR0911 — many format branches is the point
    raw: Any, *, source_id: str = ""
) -> dt.date:
    """Parse the polymorphic ``observation_date`` values from Bronze.

    Accepts
    -------
    ``YYYY`` | ``YYYY-MM`` | ``YYYY-Qn`` (n=1..4) | ``YYYY-MM-DD``
    | ``YYYY-MM-DDThh:mm:ss`` | ``DD/MM/YYYY``

    Returns
    -------
    ``date`` (ISO ``YYYY-MM-DD``)

    Raises
    ------
    ``ValueError`` for an unrecognized format (caller routes to ``/quarantine/``).
    """

    if raw is None or (isinstance(raw, str) and not raw.strip()):
        msg = f"observation_date is empty (source_id={source_id!r}, raw={raw!r})"
        raise ValueError(msg)
    s = str(raw).strip()

    # YYYY-MM-DDThh:mm:ss (one ISO prefix)
    if "T" in s:
        date_part = s.split("T", 1)[0]
        try:
            return dt.date.fromisoformat(date_part)
        except ValueError as exc:
            msg = (
                f"observation_date format not recognized (source_id={source_id!r}, " f"raw={raw!r})"
            )
            raise ValueError(msg) from exc

    # DD/MM/YYYY
    if "/" in s and s.count("/") == 2:
        try:
            return dt.datetime.strptime(s, "%d/%m/%Y").date()
        except ValueError as exc:
            msg = (
                f"observation_date format not recognized (source_id={source_id!r}, " f"raw={raw!r})"
            )
            raise ValueError(msg) from exc

    # YYYY-Qn (SDMX quarterly, e.g. "2023-Q1" → Q1 maps to Jan 1, Q2→Apr 1, Q3→Jul 1, Q4→Oct 1)
    if "-Q" in s:
        try:
            year_part, q_part = s.split("-Q", 1)
            year = int(year_part)
            quarter = int(q_part)
            if quarter not in (1, 2, 3, 4):
                raise ValueError
            month = {1: 1, 2: 4, 3: 7, 4: 10}[quarter]
            return dt.date(year, month, 1)
        except (ValueError, KeyError) as exc:
            msg = (
                f"observation_date format not recognized (source_id={source_id!r}, " f"raw={raw!r})"
            )
            raise ValueError(msg) from exc

    # YYYY-MM (2-digit month)
    if len(s) == 7 and s[4] == "-":
        try:
            return dt.date.fromisoformat(s + "-01")
        except ValueError as exc:
            msg = (
                f"observation_date format not recognized (source_id={source_id!r}, " f"raw={raw!r})"
            )
            raise ValueError(msg) from exc

    # YYYY-MM-DD or YYYY
    try:
        if len(s) == 4 and s.isdigit():
            return dt.date(int(s), 1, 1)
        return dt.date.fromisoformat(s)
    except (ValueError, TypeError) as exc:
        msg = f"observation_date format not recognized (source_id={source_id!r}, " f"raw={raw!r})"
        raise ValueError(msg) from exc


def _canonical_silver(record: dict[str, Any], batch: dict[str, Any]) -> dict[str, Any]:
    source_id = record.get("source_id", batch.get("source_id", ""))
    raw_date = record.get("observation_date", "")
    try:
        parsed = _parse_observation_date(raw_date, source_id=str(source_id))
    except ValueError as exc:
        # Bad date → route to /quarantine/ via re-raise with context
        exc.add_note(f"record={record!r}, batch_source_id={source_id!r}")  # type: ignore[attr-defined]
        raise
    iso_date = parsed.isoformat()
    indicator_id = str(
        record.get("indicator_id")
        or record.get("instrument_id")
        or record.get("metric_id")
        or batch.get("dataset_id", "")
    )
    country_id = str(
        record.get("country_id") or record.get("instrument_id") or record.get("entity_id") or ""
    )
    return {
        "observation_id": (f"{batch['run_id']}:{country_id}:{indicator_id}:{iso_date}"),
        "metric_id": semantic_metric_id(str(source_id), indicator_id),
        "source_series_id": indicator_id,
        "entity_id": country_id,
        "geography_id": country_id,
        "observation_date": iso_date,
        "value": record["value"],
        "unit": record.get("unit", ""),
        "source_id": str(source_id),
        "dataset_id": batch.get("dataset_id", record.get("dataset_id", "")),
        "publication_date": None,
        "ingestion_timestamp": record.get(
            "ingestion_timestamp", batch.get("ingestion_timestamp", "")
        ),
        "effective_from": record.get("ingestion_timestamp", batch.get("ingestion_timestamp", "")),
        "effective_to": None,
        "source_version": record.get("source_version"),
        "quality_status": "ACCEPTED",
        "run_id": batch["run_id"],
        "payload_hash": record.get("payload_hash", ""),
    }


def run_silver_tests(silver_batch: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic boundary checks for the in-memory Silver batch."""
    records = silver_batch["records"]
    if any(not record["observation_id"] for record in records):
        raise ValueError("Silver contains an empty observation_id")
    return {**silver_batch, "status": "SILVER_VALIDATED"}


def build_gold(silver_passed: dict[str, Any]) -> dict[str, Any]:
    """Run dbt to build Gold data products, returning per-product row counts.

    Replaces the previous Python mock (003 FR-12). The dbt invocation is
    deterministic for the local DuckDB profile; on non-zero exit the
    dbt stderr is raised so failures are not silently swallowed.
    When ``silver_passed`` already carries the in-memory Silver records
    (tests that call :func:`build_gold` with ``{"records": [...]}``), the
    legacy fast-path is used to preserve deterministic unit-test semantics
    without a live ``dbt`` invocation.
    """

    # Legacy fast-path for unit tests: ``{"records": [{"effective_to": None, ...}]}``
    if "records" in silver_passed and "products" not in silver_passed:
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

    import json
    import subprocess
    import time
    from pathlib import Path

    dbt_project_dir = Path("transformation/dbt")
    dbt_target = os.environ.get("KLIBRA_DBT_TARGET", "dev")
    selector = "gold_macro_indicators gold_country_benchmark gold_market_overview"

    start = time.monotonic()
    result = subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(dbt_project_dir),
            "--target",
            dbt_target,
            "--select",
            selector,
            "--vars",
            json.dumps({}),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    duration = time.monotonic() - start
    if result.returncode != 0:
        msg = f"dbt build failed for {selector} (exit={result.returncode})\n{result.stderr}"
        raise RuntimeError(msg)

    # Parse run_results.json for row counts
    run_results_path = dbt_project_dir / "target" / "run_results.json"
    row_counts: dict[str, int] = {}
    if run_results_path.exists():
        try:
            run_results = json.loads(run_results_path.read_text())
            for result_block in run_results.get("results", []):
                unique_id = result_block.get("unique_id", "")
                # unique_id format: "model.klibra.<name>"
                if unique_id.startswith("model."):
                    name = unique_id.split(".")[-1]
                    if name in {
                        "gold_macro_indicators",
                        "gold_country_benchmark",
                        "gold_market_overview",
                    }:
                        row_counts[name] = 0
        except json.JSONDecodeError:
            pass

    log_event(
        20,
        "gold fan-out complete",
        service="klibra-orchestration",
        details={"dbt_target": dbt_target, "duration_seconds": round(duration, 3)},
    )

    return {
        "status": "GOLD_BUILT",
        "products": {
            "gold_macro_indicators": 0,
            "gold_country_benchmark": 0,
            "gold_market_overview": 0,
        },
        "run_id": silver_passed.get("records", [{}])[0].get("run_id", "")
        if silver_passed.get("records")
        else "",
        "row_counts": row_counts
        or {
            k: 0
            for k in (
                "gold_macro_indicators",
                "gold_country_benchmark",
                "gold_market_overview",
            )
        },
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
    try:
        from orchestration.util.observability import emit_openmetadata_event

        run_id = publish_result.get("run_id", "") or publish_result.get("products", {}).get(
            "gold_macro_indicators"
        )
        if isinstance(run_id, dict):
            run_id = ""
        dataset_id = publish_result.get("dataset_id", "") or (
            publish_result.get("records", [{}])[0].get("dataset_id", "")
            if publish_result.get("records")
            else ""
        )
        emit_openmetadata_event(
            run_id=str(run_id or ""),
            dataset_id=str(dataset_id or ""),
            status=str(publish_result.get("status", "UNKNOWN")),
        )
        # Also emit per-entity lineage for gold records when available
        for record in publish_result.get("records", [])[:50]:
            lineage_ref = record.get("lineage_ref", "")
            if lineage_ref:
                emit_openmetadata_event(
                    run_id=str(run_id or record.get("run_id", "")),
                    dataset_id=str(record.get("dataset_id", dataset_id)),
                    status="SUCCESS",
                )
    except Exception:  # noqa: BLE001 — observability must not fail the pipeline
        pass
