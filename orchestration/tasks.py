"""Task stubs referenced by the Airflow DAG.

Each function corresponds to a DAG task and provides a minimal implementation
for local development and CI testing. Real implementations will be wired in
the appropriate user-story phase (e.g., US1 for extract, US2 for publish).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def discover_datasets() -> dict[str, Any]:
    """Discover available sources/datasets from the source catalog."""
    logger.info("discover: loading source catalog")
    return {"datasets": [], "count": 0}


def run_extraction(dataset: dict[str, Any]) -> dict[str, Any]:
    """Run a connector and persist the raw payload."""
    logger.info("extract: dataset=%s", dataset.get("id", "unknown"))
    return {"status": "pending", "dataset": dataset}


def validate_raw(extraction: dict[str, Any]) -> dict[str, Any]:
    """Validate the raw payload is well-formed and hashable."""
    logger.info("raw_validation: extraction=%s", extraction.get("status"))
    return {"status": "pending", "extraction": extraction}


def build_bronze(validation: dict[str, Any]) -> dict[str, Any]:
    """Parse source-aligned records into Bronze."""
    logger.info("bronze: validation=%s", validation.get("status"))
    return {"status": "pending", "validation": validation}


def apply_quality_gate(bronze_batch: dict[str, Any]) -> dict[str, Any]:
    """Apply quality framework; quarantine P0/P1 failures."""
    logger.info("quality_gate: bronze_batch=%s", bronze_batch.get("status"))
    return {"status": "pending", "bronze_batch": bronze_batch}


def build_silver(quality_passed: dict[str, Any]) -> dict[str, Any]:
    """Standardize to fact_economic_observation + dimensions."""
    logger.info("silver: quality_passed=%s", quality_passed.get("status"))
    return {"status": "pending", "quality_passed": quality_passed}


def run_silver_tests(silver_batch: dict[str, Any]) -> dict[str, Any]:
    """Run dbt tests on Silver models."""
    logger.info("silver_quality: silver_batch=%s", silver_batch.get("status"))
    return {"status": "pending", "silver_batch": silver_batch}


def build_gold(silver_passed: dict[str, Any]) -> dict[str, Any]:
    """Run dbt to build Gold data products."""
    logger.info("gold: silver_passed=%s", silver_passed.get("status"))
    return {"status": "pending", "silver_passed": silver_passed}


def publish_gold(gold_batch: dict[str, Any]) -> dict[str, Any]:
    """Publish Gold products to the serving layer."""
    logger.info("publish: gold_batch=%s", gold_batch.get("status"))
    return {"status": "pending", "gold_batch": gold_batch}


def notify_owners(publish_result: dict[str, Any]) -> None:
    """Send alerts and notifications to responsible owners."""
    logger.info("notify: publish_result=%s", publish_result.get("status"))
