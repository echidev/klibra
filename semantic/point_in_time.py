"""Point-in-time query helpers — TDD §12, §70, Constitution §XIII.

Provides a convenience API for Data Scientists and downstream consumers
to retrieve a snapshot of Gold products as they were known at a given
``as_of_timestamp`` (point-in-time / SCD-2 semantics).

Usage (SQL form, direct reuse in dbt models)::

    -- Return only current facts as of 2023-12-31
    SELECT *
    FROM silver.fact_economic_observation
    WHERE effective_from <= :as_of_timestamp
      AND (effective_to IS NULL OR effective_to > :as_of_timestamp)

Usage (Python form)::

    from semantic.point_in_time import as_of_predicate, filter_as_of

    sql_fragment = as_of_predicate("2023-12-31T00:00:00Z")
    records = filter_as_of(records, "2023-12-31T00:00:00Z")
"""

from __future__ import annotations

import datetime as dt
from typing import Any

__all__ = ["as_of_predicate", "filter_as_of"]


def as_of_predicate(as_of_timestamp: str) -> str:
    """Return a SQL WHERE fragment for an as‑of query (SCD-2).

    ``as_of_timestamp`` is an ISO 8601 string; the caller is responsible
    for validating it.
    """
    safe_ts = as_of_timestamp.replace("'", "''")
    return (
        f"effective_from <= '{safe_ts}' "
        f"AND (effective_to IS NULL OR effective_to > '{safe_ts}')"
    )


def filter_as_of(
    records: list[dict[str, Any]],
    as_of_timestamp: str,
    *,
    grain_key: str = "observation_date",
) -> list[dict[str, Any]]:
    """Filter a list of SCD-2 records to an as‑of snapshot.

    Parameters
    ----------
    records:
        A list of fact dicts that carry ``effective_from`` /
        ``effective_to``.
    as_of_timestamp:
        ISO 8601 timestamp to snapshot at.
    grain_key:
        The grain identifier (unused for filtering; returned records
        preserve their original grain).

    Returns
    -------
    list[dict[str, Any]]
        The subset of records valid at ``as_of_timestamp`` (at most one
        per physical grain after ``effective_to`` closure).
    """
    cutoff = dt.datetime.fromisoformat(as_of_timestamp.replace("Z", "+00:00"))
    result: list[dict[str, Any]] = []
    for rec in records:
        ef = dt.datetime.fromisoformat(str(rec.get("effective_from", "")).replace("Z", "+00:00"))
        et_raw = rec.get("effective_to")
        et = (
            None
            if et_raw is None
            else dt.datetime.fromisoformat(str(et_raw).replace("Z", "+00:00"))
        )
        if ef <= cutoff and (et is None or et > cutoff):
            result.append(rec)
    return result
