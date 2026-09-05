"""Opt-in live end-to-end test for World Bank Raw -> Gold processing."""

from __future__ import annotations

import os

import pytest

from ingestion.connectors.worldbank import WorldBankConnector
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


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("KLIBRA_RUN_LIVE_E2E") != "1",
    reason="set KLIBRA_RUN_LIVE_E2E=1 to run the live World Bank test",
)
def test_live_worldbank_pipeline() -> None:
    connector = WorldBankConnector(dataset_id="NY.GDP.MKTP.KD.ZG")
    extracted = run_extraction(
        {"datasets": [{"source_id": "worldbank", "dataset_id": "NY.GDP.MKTP.KD.ZG"}]},
        connector_factory=lambda _definition: connector,
    )
    quality = apply_quality_gate(build_bronze(validate_raw(extracted)))
    gold = publish_gold(build_gold(run_silver_tests(build_silver(quality))))

    assert gold["status"] == "PUBLISHED"
    assert gold["records_written"] > 0
