"""klibra_pipeline — KLIBRA canonical DAG (TDD §25, plan.md).

Task graph per TDD §25::

    discover → extract → raw_validation → bronze
    → quality_gate → silver → silver_quality → gold
    → publish → notify

Each task is independently observable and retryable. Cross-cutting
responsibilities (run-state writes, metrics emission, alert routing) live
in dedicated utility modules — kept out of this DAG file to keep the
control flow readable.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

try:
    from airflow.decorators import dag, task
    from airflow.operators.empty import EmptyOperator
    from airflow.utils.trigger_rule import TriggerRule
except ModuleNotFoundError:  # pragma: no cover - only used outside Airflow

    class _FallbackTask:
        def __init__(self, callable_: Any) -> None:
            self.callable = callable_

        def __call__(self, *_args: Any, **_kwargs: Any) -> _FallbackTask:
            return self

        def __rshift__(self, other: Any) -> Any:
            return other

    def task(**_kwargs: Any) -> Any:
        def decorator(callable_: Any) -> _FallbackTask:
            return _FallbackTask(callable_)

        return decorator

    def dag(**_kwargs: Any) -> Any:
        def decorator(callable_: Any) -> Any:
            return callable_

        return decorator

    class EmptyOperator(_FallbackTask):  # type: ignore[no-redef]
        def __init__(self, **_kwargs: Any) -> None:
            super().__init__(lambda: None)

    class TriggerRule:  # type: ignore[no-redef]
        ALL_DONE = "all_done"


__all__ = ["klibra_pipeline"]

DAG_ID = "klibra_pipeline"
DEFAULT_ARGS: dict[str, Any] = {
    "owner": "klibra-data-platform",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": dt.timedelta(minutes=5),
    "execution_timeout": dt.timedelta(hours=1),
    "email_on_failure": False,
}


@dag(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="KLIBRA canonical pipeline: discover → extract → raw → bronze → silver → gold",
    schedule="@daily",
    start_date=dt.datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    tags=["klibra", "pipeline", "release-1"],
)
def klibra_pipeline() -> None:
    """Compose the canonical KLIBRA DAG."""

    @task(task_id="discover")
    def discover() -> dict[str, Any]:
        """Enumerate eligible sources/datasets from the source catalog."""
        from orchestration.tasks import discover_datasets

        return discover_datasets()

    @task(task_id="extract")
    def extract(dataset: dict[str, Any]) -> dict[str, Any]:
        """Run connectors and persist raw payloads to mandatory storage."""
        from orchestration.tasks import run_extraction
        from orchestration.util.storage import make_storage_client, make_storage_writer

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
        from orchestration.tasks import build_bronze

        return build_bronze(validation)

    @task(task_id="quality_gate")
    def quality_gate(bronze_batch: dict[str, Any]) -> dict[str, Any]:
        """Apply four-level quality framework; quarantine P0/P1 failures."""
        from orchestration.tasks import apply_quality_gate

        return apply_quality_gate(bronze_batch)

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
            logging.warning("backfill: failed_validation run_id=%s errors=%s", req.run_id, errors)
            return {"status": "REJECTED", "errors": errors}
        receipt = BackfillOrchestrator().submit(req)
        logging.info(
            "backfill: submitted run_id=%s idempotency_key=%s",
            receipt.get("run_id"),
            receipt.get("idempotency_key"),
        )
        return {"status": "SUBMITTED", **receipt}

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
        for k in ("gold_macro_indicators", "gold_country_benchmark", "gold_market_overview"):
            for row in gold_batch.get(k, {}).get("records", []) or gold_batch.get("records", []):
                records.append(row)
        # Also accept flat record list on gold_batch (fallback for mocks)
        if not records and isinstance(gold_batch.get("records"), list):
            records = gold_batch["records"]

        # Group by entity_id as a minimal Gold → intelligence input shape.
        # Fallback when gold has no entity: use a single entity "all".
        by_entity: dict[str, list[dict[str, Any]]] = {}
        for row in records or []:
            entity = (row.get("entity_id") or row.get("observation_id", "all")).split(":")[0]
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
            for entity_id, entity_records in (by_entity or {"all": []}).items():
                inputs: dict[str, float] = {}
                for k in scorer.weights:
                    # Prefer metric match in gold; fall back to recent value.
                    for row in entity_records:
                        if row.get("metric_id") == k and row.get("value") is not None:
                            inputs[k] = float(row["value"])
                            break
                score_obj = scorer.score(inputs)
                persist_quality = (
                    "QUARANTINED"
                    if score_obj.coverage_ratio < scorer.__dict__.get("min_coverage", 0.5)
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
                intelligence.setdefault(product_id, []).append(persisted)
                scores.append(
                    {"product_id": product_id, "entity_id": entity_id, "score": persisted}
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
        publish_result["intelligence"] = intelligence_batch.get("intelligence", {})
        return publish_result

    @task(task_id="notify")
    def notify(publish_result: dict[str, Any]) -> None:
        """Route run state, metrics, and alerts to owners.

        Emits an OpenMetadata lineage event and a CloudWatch alarm payload
        per TDD §30 (publish/notify).
        """
        from orchestration.tasks import notify_owners
        from orchestration.util.observability import (
            emit_cloudwatch_alarm,
            emit_openmetadata_event,
        )

        run_id = publish_result.get("gold_batch", {}).get("run_id", "")
        dataset_id = publish_result.get("gold_batch", {}).get("dataset_id", "")
        status = publish_result.get("status", "UNKNOWN")
        notify_owners(publish_result)
        emit_openmetadata_event(run_id=run_id, dataset_id=dataset_id, status=status)
        emit_cloudwatch_alarm(
            payload={
                "run_id": run_id,
                "dataset_id": dataset_id,
                "status": status,
            }
        )

    # ── Wire the graph ─────────────────────────────────────
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

    # Terminal catch-all in case notify is bypassed.
    finalize = EmptyOperator(
        task_id="finalize",
        trigger_rule=TriggerRule.ALL_DONE,
    )
    pu >> finalize


dag_instance = klibra_pipeline()
