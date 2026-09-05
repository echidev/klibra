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
        """Run connectors and persist raw payloads."""
        from orchestration.tasks import run_extraction

        return run_extraction(dataset)

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

    @task(task_id="publish")
    def publish(gold_batch: dict[str, Any]) -> dict[str, Any]:
        """Make Gold products discoverable to consumers."""
        from orchestration.tasks import publish_gold

        return publish_gold(gold_batch)

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
    pu = publish(go)
    notify(pu)

    # Terminal catch-all in case notify is bypassed.
    finalize = EmptyOperator(
        task_id="finalize",
        trigger_rule=TriggerRule.ALL_DONE,
    )
    pu >> finalize


dag_instance = klibra_pipeline()
