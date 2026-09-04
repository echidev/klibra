"""SCD-2 invariant tests — TDD §12, Constitution §XIII, plan.md.

Enforces: at‑most‑one current row per
``(metric_id, entity_id, geography_id, sector_id, observation_date, source_id, dataset_id, source_version)``.

Implemented as a pure‑Python contract test so it can run locally and in CI
without a live PostgreSQL or Silver layer.
"""

from __future__ import annotations

from typing import Any

import pytest

# TDD §12 — canonical SCD-2 grain
SCD2_GRANULE: tuple[str, ...] = (
    "metric_id",
    "entity_id",
    "geography_id",
    "sector_id",
    "observation_date",
    "source_id",
    "dataset_id",
    "source_version",
)


def check_scd2_invariant(records: list[dict[str, Any]]) -> list[str]:
    """Return a list of violations (empty if the set satisfies SCD-2).

    A violation occurs when two records share the same ``SCD2_GRANULE`` key
    and both have ``effective_to is None`` (two current versions at the
    same point‑in‑time).
    """
    current_groups: dict[tuple[str, ...], int] = {}
    violations: list[str] = []
    for rec in records:
        key = tuple(str(rec.get(k, "")) for k in SCD2_GRANULE)
        if rec.get("effective_to") is None:
            if key in current_groups:
                violations.append(f"duplicate current row for grain {key!r}")
            current_groups[key] = current_groups.get(key, 0) + 1
    return violations


@pytest.mark.contract
def test_scd2_invariant_accepts_single_current_row() -> None:
    now = "2023-01-01T00:00:00Z"
    rec = {
        "observation_id": "o1",
        "metric_id": "gdp_growth_rate",
        "entity_id": "USA",
        "geography_id": "USA",
        "sector_id": "gdp",
        "observation_date": "2023-01-01",
        "value": 2.5,
        "unit": "pct",
        "source_id": "worldbank",
        "dataset_id": "NY.GDP.MKTP.CD",
        "effective_from": now,
        "effective_to": None,
        "source_version": None,
        "quality_status": "ACCEPTED",
    }
    assert check_scd2_invariant([rec]) == []


@pytest.mark.contract
def test_scd2_invariant_rejects_two_current_rows_with_same_grain() -> None:
    now = "2023-01-01T00:00:00Z"
    base = {
        "observation_id": "o1",
        "metric_id": "gdp_growth_rate",
        "entity_id": "USA",
        "geography_id": "USA",
        "sector_id": "gdp",
        "observation_date": "2023-01-01",
        "value": 2.5,
        "unit": "pct",
        "source_id": "worldbank",
        "dataset_id": "NY.GDP.MKTP.CD",
        "effective_from": now,
        "effective_to": None,
        "source_version": None,
        "quality_status": "ACCEPTED",
    }
    rec1 = dict(base, observation_id="o1")
    rec2 = dict(base, observation_id="o2")
    assert len(check_scd2_invariant([rec1, rec2])) == 1


@pytest.mark.contract
def test_scd2_invariant_allows_closed_prior_version() -> None:
    now = "2023-01-01T00:00:00Z"
    later = "2023-02-01T00:00:00Z"
    base = {
        "metric_id": "gdp_growth_rate",
        "entity_id": "USA",
        "geography_id": "USA",
        "sector_id": "gdp",
        "observation_date": "2023-01-01",
        "value": 2.5,
        "unit": "pct",
        "source_id": "worldbank",
        "dataset_id": "NY.GDP.MKTP.CD",
        "source_version": None,
        "quality_status": "ACCEPTED",
    }
    closed = dict(base, observation_id="o1", effective_from=now, effective_to=later)
    current = dict(base, observation_id="o2", effective_from=later, effective_to=None)
    assert check_scd2_invariant([closed, current]) == []
