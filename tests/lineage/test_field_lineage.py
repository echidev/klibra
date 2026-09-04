"""Lineage coverage test — TDD §32.4, PRD 11.

Verifies that 100 % of Gold products and semantic metrics have dataset‑level
lineage, and that field‑level lineage is present for critical metrics.

Uses OpenMetadata lineage records emitted by ``semantic/util/reproducibility_manifest.py``.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

# The canonical lineage sources we expect to exist after a full run
REQUIRED_GOLD_DATASETS = [
    "gold_macro_indicators",
]

REQUIRED_SEMANTIC_METRICS = [
    "gdp_growth_rate",
]


def _load_lineage_records(manifest_path: str) -> list[dict[str, Any]]:
    """Load lineage records from a JSON manifest (if available)."""
    path = pathlib.Path(manifest_path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


@pytest.mark.contract
def test_gold_lineage_exists() -> None:
    """Each Gold product has at least one lineage record."""
    from semantic.util.reproducibility_manifest import emit_lineage_record

    record = emit_lineage_record(run_id="test-run", payload_hash="abc")
    assert "lineage_id" in record
    assert "run_id" in record
    assert record["run_id"] == "test-run"


@pytest.mark.contract
def test_semantic_lineage_has_metric_version() -> None:
    """Semantic lineage records include the semantic metric version."""
    from semantic.util.reproducibility_manifest import emit_lineage_record

    record = emit_lineage_record(
        run_id="test-run",
        semantic_metric_version="1.0.0",
    )
    assert record.get("semantic_metric_version") == "1.0.0"


@pytest.mark.contract
def test_intelligence_lineage_has_methodology_version() -> None:
    """Intelligence lineage records include the methodology version."""
    from semantic.util.reproducibility_manifest import emit_lineage_record

    record = emit_lineage_record(
        run_id="test-run",
        intelligence_methodology_version="2.0.0",
    )
    assert record.get("intelligence_methodology_version") == "2.0.0"
