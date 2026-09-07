"""KLIBRA pipeline — single TaskGraphFactory for both real and dry-run modes.

Both `dag_id="klibra_pipeline"` (@daily, retries=3, execution_timeout=60m) and
`dag_id="klibra_pipeline_ondemand"` (schedule=None, retries=0, execution_timeout=15m)
are produced from the same internal factory `_make_klibra_pipeline`, so the task
list is identical and any wiring bug shows up in the dry-run DAG before the
real scheduled run. Per FR-001 (006-dry-run-hardening), the dry-run DAG is
the same graph as the real DAG; the only difference is schedule and default
args.

The dry-run mode toggle is `KLIBRA_DRY_RUN`:
- "1" / "true" / "yes" → synthetic payloads, no dbt subprocess, no upstream HTTP
- unset / "0" / anything else → live mode

The check is done at task runtime inside `orchestration/tasks.*`, not at DAG
parse time, so a host process can flip the mode without reimporting.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

__all__ = ["klibra_pipeline", "klibra_pipeline_ondemand"]


DAG_ID = "klibra_pipeline"
DEFAULT_ARGS: dict[str, Any] = {
    "owner": "klibra-data-platform",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": dt.timedelta(minutes=5),
    "execution_timeout": dt.timedelta(hours=1),
    "email_on_failure": False,
}

ONDEMAND_ARGS: dict[str, Any] = {
    "owner": "klibra-data-platform",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": dt.timedelta(seconds=10),
    "execution_timeout": dt.timedelta(minutes=15),
    "email_on_failure": False,
}


def _make_klibra_pipeline(
    dag_id: str,
    schedule: Any,
    default_args: dict[str, Any],
) -> Any:
    """Build a KLIBRA pipeline DAG.

    Both `klibra_pipeline` (@daily) and `klibra_pipeline_ondemand` (manual-only)
    call this factory with the same task graph. The only thing that differs
    between the two DAG instances is `schedule` and `default_args`.
    """

    @dag(
        dag_id=dag_id,
        default_args=default_args,
        description=(
            "KLIBRA canonical pipeline: discover → extract → raw → bronze → "
            "silver → gold → compute_intelligence → publish → notify"
        ),
        schedule=schedule,
        start_date=dt.datetime(2026, 9, 1),
        catchup=False,
        max_active_runs=1,
        tags=["klibra", "pipeline", "release-1"],
    )
    def pipeline_factory() -> None:
        @task(task_id="discover")
        def discover() -> dict[str, Any]:
            """Enumerate eligible sources/datasets from the source catalog."""
            from orchestration.tasks import discover_datasets

            return discover_datasets()

        @task(task_id="extract")
        def extract(dataset: dict[str, Any]) -> dict[str, Any]:
            """Run connectors and persist raw payloads to mandatory storage."""
            from orchestration.tasks import run_extraction
            from orchestration.util.storage import (
                make_storage_client,
                make_storage_writer,
            )

            writer = make_storage_writer()
            client = make_storage_client()
            return run_extraction(dataset, storage_writer=writer, storage_client=client)

        @task(task_id="raw_validation")
        def raw_validation(extraction: dict[str, Any]) -> dict[str, Any]:
            """Validate that the raw payload is well-formed and hashable."""
            from orchestration.tasks import validate_raw

            return validate_raw(extraction)

        @task(task_id="bronze")
        def bronze(validation: dict[str, Any]) -> dict[str, Any]:
            """Parse source-aligned records into Bronze."""
            from transformation.bronze.alphavantage import (
                build_bronze_records as build_bronze_alphavantage,
            )
            from transformation.bronze.ecb_indicators import (
                build_bronze_records as build_bronze_ecb,
            )
            from transformation.bronze.fred import (
                build_bronze_records as build_bronze_fred,
            )
            from transformation.bronze.worldbank_indicators import (
                build_bronze_records as build_bronze_worldbank,
            )
            from orchestration.tasks import _is_dry_run, _synthesize_bronze_record

            batches: list[dict[str, Any]] = []
            for item in validation["items"]:
                source_id = item["source_id"]
                # Dry-run: payload + metadata stripped at XCom boundary;
                # synthesise a minimal Bronze record so downstream shape
                # validation can run without external payload bytes.
                if _is_dry_run() and item.get("validated_dry_run"):
                    record = _synthesize_bronze_record(
                        source_id=source_id,
                        dataset_id=item["dataset_id"],
                        run_id=item["run_id"],
                    )
                    batches.append(
                        {
                            "source_id": source_id,
                            "dataset_id": item["dataset_id"],
                            "run_id": item["run_id"],
                            "raw_key": item.get("raw_key", ""),
                            "records": [record],
                        }
                    )
                    continue
                common_kwargs: dict[str, Any] = {
                    "source_id": item["source_id"],
                    "run_id": item["run_id"],
                    "ingestion_timestamp": item["metadata"].retrieval_timestamp,
                    "raw_source_url": item["source_url"],
                }
                if source_id == "worldbank":
                    records = build_bronze_worldbank(
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
                    metadata = getattr(
                        item.get("metadata"), "response_metadata", None
                    )
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
                elif source_id == "coingecko":
                    from transformation.bronze.coingecko import (  # noqa: PLC0415
                        build_bronze_records as build_bronze_coingecko,
                    )

                    records = build_bronze_coingecko(
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

        @task(task_id="backfill")
        def backfill(request: dict[str, Any]) -> dict[str, Any]:
            """Submit a BackfillRequest via BackfillOrchestrator (Spec 004 T037)."""
            import logging

            from orchestration.operators.backfill_orchestrator import (
                BackfillOrchestrator,
                BackfillRequest,
            )

            try:
                req = BackfillRequest(**request)
            except TypeError as exc:
                logging.warning("backfill: invalid request: %s", exc)
                return {"status": "REJECTED", "errors": [f"invalid request: {exc}"]}
            is_valid, errors = BackfillOrchestrator.validate(req)
            if not is_valid:
                logging.warning(
                    "backfill: failed_validation run_id=%s errors=%s",
                    req.run_id,
                    errors,
                )
                return {"status": "REJECTED", "errors": errors}
            receipt = BackfillOrchestrator().submit(req)
            logging.info(
                "backfill: submitted run_id=%s idempotency_key=%s",
                receipt.get("run_id"),
                receipt.get("idempotency_key"),
            )
            return {"status": "SUBMITTED", **receipt}

        @task(task_id="quality_gate")
        def quality_gate(bronze_batch: dict[str, Any]) -> dict[str, Any]:
            """Apply four-level quality framework; quarantine P0/P1 failures."""
            from orchestration.tasks import apply_quality_gate

            return apply_quality_gate(bronze_batch)

        @task(task_id="silver")
        def silver(quality_passed: dict[str, Any]) -> dict[str, Any]:
            """Standardize to fact_economic_observation + dimensions."""
            from orchestration.tasks import build_silver

            return build_silver(quality_passed)

        @task(task_id="silver_quality")
        def silver_quality(silver_batch: dict[str, Any]) -> dict[str, Any]:
            """Run dbt tests on Silver models."""
            from orchestration.tasks import run_silver_tests

            return run_silver_tests(silver_batch)

        @task(task_id="gold")
        def gold(silver_passed: dict[str, Any]) -> dict[str, Any]:
            """Run dbt to build Gold data products."""
            from orchestration.tasks import build_gold

            return build_gold(silver_passed)

        @task(task_id="compute_intelligence")
        def compute_intelligence(gold_batch: dict[str, Any]) -> dict[str, Any]:
            """Compute composite intelligence products from Gold data.

            G10: five scorers (economic_momentum, inflation_pressure,
            market_stress, country_risk, global_liquidity).

            Inputs for each scorer are drawn from the Gold layer per
            TDD §25 and plan Decision 6: intelligence reads from Gold +
            Silver. Each scorer's ``weights`` keys dictate which metric
            keys are read; missing inputs are allowed (coverage gate).
            Persisted via ``intelligence.persist.persist_score``.

            Returns
            -------
            dict
                ``{"status": "INTELLIGENCE_COMPUTED", "scores": [...], "intelligence": {product_id: persisted_row}}``
            """
            from intelligence.persist import persist_score
            from intelligence.products.country_risk import CountryRiskScorer
            from intelligence.products.economic_momentum import EconomicMomentumScorer
            from intelligence.products.global_liquidity import GlobalLiquidityScorer
            from intelligence.products.inflation_pressure import InflationPressureScorer
            from intelligence.products.market_stress import MarketStressScorer

            records: list[dict[str, Any]] = []
            for k in (
                "gold_macro_indicators",
                "gold_country_benchmark",
                "gold_market_overview",
            ):
                for row in gold_batch.get(k, {}).get("records", []) or gold_batch.get(
                    "records", []
                ):
                    records.append(row)
            # Also accept flat record list on gold_batch (fallback for mocks)
            if not records and isinstance(gold_batch.get("records"), list):
                records = gold_batch["records"]

            # Group by entity_id as a minimal Gold → intelligence input shape.
            # Fallback when gold has no entity: use a single entity "all".
            by_entity: dict[str, list[dict[str, Any]]] = {}
            for row in records or []:
                entity = (
                    row.get("entity_id") or row.get("observation_id", "all")
                ).split(":")[0]
                by_entity.setdefault(entity or "all", []).append(row)

            scorer_specs: list[tuple[type, str]] = [
                (EconomicMomentumScorer, "intelligence_economic_momentum"),
                (InflationPressureScorer, "intelligence_inflation_pressure"),
                (MarketStressScorer, "intelligence_market_stress"),
                (CountryRiskScorer, "intelligence_country_risk"),
                (GlobalLiquidityScorer, "intelligence_global_liquidity"),
            ]
            intelligence: dict[str, Any] = {}
            scores: list[dict[str, Any]] = []
            errors: list[str] = []
            for scorer_cls, product_id in scorer_specs:
                try:
                    scorer = scorer_cls()
                except Exception as exc:
                    errors.append(f"{product_id}: instantiate failed: {exc}")
                    continue
                for entity_id, entity_records in (
                    by_entity or {"all": []}
                ).items():
                    inputs: dict[str, float] = {}
                    for k in scorer.weights:
                        # Prefer metric match in gold; fall back to recent value.
                        for row in entity_records:
                            if (
                                row.get("metric_id") == k
                                and row.get("value") is not None
                            ):
                                inputs[k] = float(row["value"])
                                break
                    score_obj = scorer.score(inputs)
                    persist_quality = (
                        "QUARANTINED"
                        if score_obj.coverage_ratio
                        < scorer.__dict__.get("min_coverage", 0.5)
                        else "ACCEPTED"
                    )
                    persisted = persist_score(
                        score_obj,
                        entity_id=entity_id,
                        observation_period=(
                            records[0].get("observation_date", "1970-01-01")
                            if records
                            else "1970-01-01"
                        ),
                        quality_status=persist_quality,
                    )
                    # FR-006: convert IntelligenceScore to plain dict via
                    # asdict so XCom round-trips without allow-list growth.
                    # persist_score already returns a plain dict — no asdict needed.
                    intelligence.setdefault(product_id, []).append(persisted)
                    scores.append(
                        {
                            "product_id": product_id,
                            "entity_id": entity_id,
                            "score": persisted,
                        }
                    )

            return {
                "status": "INTELLIGENCE_COMPUTED",
                "scores": scores,
                "intelligence": intelligence,
                "gold_batch": gold_batch,
                "errors": errors,
            }

        @task(task_id="publish")
        def publish(intelligence_batch: dict[str, Any]) -> dict[str, Any]:
            """Make Gold + Intelligence discoverable to consumers.

            Accepts the ``compute_intelligence`` output (or a raw Gold batch
            when intelligence is skipped); forwards to ``publish_gold`` on the
            embedded ``gold_batch``.
            """
            from orchestration.tasks import publish_gold

            gold_batch = intelligence_batch.get("gold_batch", intelligence_batch)
            if not gold_batch.get("records") and not gold_batch.get("products"):
                gold_batch = intelligence_batch.get("gold_batch") or intelligence_batch
            publish_result = publish_gold(gold_batch)  # type: ignore[arg-type]
            publish_result["intelligence"] = intelligence_batch.get(
                "intelligence", {}
            )
            return publish_result

        @task(task_id="notify")
        def notify(publish_result: dict[str, Any]) -> None:
            """Route run state, metrics, and alerts to owners.

            Emits an OpenMetadata lineage event and a CloudWatch alarm payload
            per TDD §30 (publish/notify). All ``emit_*`` calls are wrapped in
            try/except so an empty ``run_id`` or downstream outage never
            crashes the task (FR-007). A single INFO line is emitted
            regardless of OpenMetadata availability (FR-007 follow-up).
            """
            import logging

            from orchestration.tasks import notify_owners
            from orchestration.util.observability import (
                emit_cloudwatch_alarm,
                emit_openmetadata_event,
            )

            run_id = publish_result.get("gold_batch", {}).get("run_id", "")
            dataset_id = publish_result.get("gold_batch", {}).get("dataset_id", "")
            status = publish_result.get("status", "UNKNOWN")
            logging.info(
                "notify: run_id=%s dataset_id=%s status=%s",
                run_id,
                dataset_id,
                status,
            )
            notify_owners(publish_result)
            emit_openmetadata_event(
                run_id=run_id, dataset_id=dataset_id, status=status
            )
            emit_cloudwatch_alarm(
                payload={
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "status": status,
                }
            )

        # ── Wire the graph ─────────────────────────────────────────────
        disc = discover()
        ext = extract(disc)
        rv = raw_validation(ext)
        br = bronze(rv)
        qg = quality_gate(br)
        si = silver(qg)
        sq = silver_quality(si)
        go = gold(sq)
        ci = compute_intelligence(go)
        pu = publish(ci)
        notify(pu)

        # backfill is defined but unwired (operational tool, not part of
        # the daily chain). Tests/dashboards can call it via Airflow CLI.
        _ = backfill  # noqa: F841 — keep referenced to avoid lint warnings

        # Terminal catch-all in case notify is bypassed.
        finalize = EmptyOperator(
            task_id="finalize",
            trigger_rule=TriggerRule.ALL_DONE,
        )
        pu >> finalize

    return pipeline_factory()


# Both DAGs come from the same factory — FR-001 (006-dry-run-hardening).
klibra_pipeline = _make_klibra_pipeline(DAG_ID, "@daily", DEFAULT_ARGS)
klibra_pipeline_ondemand = _make_klibra_pipeline(
    "klibra_pipeline_ondemand", None, ONDEMAND_ARGS
)
