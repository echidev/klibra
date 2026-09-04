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

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

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
        from ingestion.orchestration.tasks import discover_datasets

        return discover_datasets()

    @task(task_id="extract")
    def extract(dataset: dict[str, Any]) -> dict[str, Any]:
        """Run connectors and persist raw payloads."""
        from ingestion.orchestration.tasks import run_extraction

        return run_extraction(dataset)

    @task(task_id="raw_validation")
    def raw_validation(extraction: dict[str, Any]) -> dict[str, Any]:
        """Validate that the raw payload is well-formed and hashable."""
        from ingestion.orchestration.tasks import validate_raw

        return validate_raw(extraction)

    @task(task_id="bronze")
    def bronze(validation: dict[str, Any]) -> dict[str, Any]:
        """Parse source-aligned records into Bronze."""
        from ingestion.orchestration.tasks import build_bronze

        return build_bronze(validation)

    @task(task_id="quality_gate")
    def quality_gate(bronze_batch: dict[str, Any]) -> dict[str, Any]:
        """Apply four-level quality framework; quarantine P0/P1 failures."""
        from ingestion.orchestration.tasks import apply_quality_gate

        return apply_quality_gate(bronze_batch)

    @task(task_id="silver")
    def silver(quality_passed: dict[str, Any]) -> dict[str, Any]:
        """Standardize to fact_economic_observation + dimensions."""
        from ingestion.orchestration.tasks import build_silver

        return build_silver(quality_passed)

    @task(task_id="silver_quality")
    def silver_quality(silver_batch: dict[str, Any]) -> dict[str, Any]:
        """Run dbt tests on Silver models."""
        from ingestion.orchestration.tasks import run_silver_tests

        return run_silver_tests(silver_batch)

    @task(task_id="gold")
    def gold(silver_passed: dict[str, Any]) -> dict[str, Any]:
        """Run dbt to build Gold data products."""
        from ingestion.orchestration.tasks import build_gold

        return build_gold(silver_passed)

    @task(task_id="publish")
    def publish(gold_batch: dict[str, Any]) -> dict[str, Any]:
        """Make Gold products discoverable to consumers."""
        from ingestion.orchestration.tasks import publish_gold

        return publish_gold(gold_batch)

    @task(task_id="notify")
    def notify(publish_result: dict[str, Any]) -> None:
        """Route run state, metrics, and alerts to owners."""
        from ingestion.orchestration.tasks import notify_owners

        notify_owners(publish_result)

    # ── Wire the graph ─────────────────────────────────────
    disc = discover()
    ext = extract(disc)
    rv = raw_validation(ext)
    br = bronze(rv)
    qg = quality_gate(br)
    si = silver(qg)
    sq = silver_quality(si)
    go = gold(sq)
    pu = publish(go)
    notify(pu)

    # Terminal catch-all in case notify is bypassed
    EmptyOperator(
        task_id="finalize",
        trigger_rule=TriggerRule.ALL_DONE,
    ).set_downstream(pu)


dag_instance = klibra_pipeline()
