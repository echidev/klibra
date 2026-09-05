"""Cross-source reconciler — PRD UC-03, plan.md Decision 7.

Compares two source streams on the shared grain
(metric_id, entity_id, observation_date) and reports per-cell diff
(absolute, sign, percent) plus a divergence flag when definitions
disagree beyond a configurable threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["Reconciler", "ReconcileRow", "ReconcileResult"]


@dataclass(frozen=True, slots=True)
class ReconcileRow:
    metric_id: str
    entity_id: str
    observation_date: str
    value_a: float | None
    value_b: float | None
    diff_absolute: float | None
    diff_percent: float | None
    sign: str | None  # "a_higher" / "b_higher" / "equal" / "incomparable"
    divergent: bool


@dataclass(slots=True)
class ReconcileResult:
    rows: list[ReconcileRow]
    divergence_count: int = 0
    divergence_rate: float = 0.0  # divergence_count / len(rows)


class Reconciler:
    """Reconcile two source streams on a shared grain.

    Parameters
    ----------
    divergence_threshold_percent:
        Absolute percent difference beyond which a row is flagged as
        divergent (i.e. the two sources disagree materially).
    """

    def __init__(self, *, divergence_threshold_percent: float = 20.0) -> None:
        self.divergence_threshold_percent = divergence_threshold_percent

    def _diff(
        self, value_a: float | None, value_b: float | None
    ) -> tuple[float | None, float | None, str | None, bool]:
        if value_a is None or value_b is None:
            return (None, None, "incomparable", False)
        diff_abs = value_a - value_b
        denom = max(abs(value_b), 1e-9)
        diff_pct = diff_abs / denom * 100.0
        if abs(diff_abs) < 1e-9:
            sign = "equal"
        elif diff_abs > 0:
            sign = "a_higher"
        else:
            sign = "b_higher"
        divergent = abs(diff_pct) > self.divergence_threshold_percent
        return (diff_abs, diff_pct, sign, divergent)

    def reconcile(
        self,
        source_a: list[dict[str, Any]],
        source_b: list[dict[str, Any]],
        *,
        grain_keys: tuple[str, ...] = ("metric_id", "entity_id", "observation_date"),
    ) -> ReconcileResult:
        """Return a ``ReconcileResult`` for two source streams.

        Each list element is a dict with at least ``metric_id``,
        ``entity_id``, ``observation_date``, ``value``. Streams are joined
        on ``grain_keys`` via inner join; missing grain entries are
        reported as incomparable.
        """
        # Build index on grain
        index_a: dict[tuple[str, ...], dict[str, Any]] = {}
        index_b: dict[tuple[str, ...], dict[str, Any]] = {}
        for row in source_a:
            key = tuple(str(row.get(k, "")) for k in grain_keys)
            index_a[key] = row
        for row in source_b:
            key = tuple(str(row.get(k, "")) for k in grain_keys)
            index_b[key] = row

        all_keys: set[tuple[str, ...]] = set(index_a) | set(index_b)
        rows: list[ReconcileRow] = []
        divergence_count = 0
        for key in sorted(all_keys):
            ra = index_a.get(key)
            rb = index_b.get(key)
            metric_id, entity_id, observation_date = key
            value_a = ra.get("value") if ra else None
            value_b = rb.get("value") if rb else None
            diff_abs, diff_pct, sign, divergent = self._diff(value_a, value_b)
            if divergent:
                divergence_count += 1
            rows.append(
                ReconcileRow(
                    metric_id=metric_id,
                    entity_id=entity_id,
                    observation_date=observation_date,
                    value_a=value_a,
                    value_b=value_b,
                    diff_absolute=diff_abs,
                    diff_percent=diff_pct,
                    sign=sign,
                    divergent=divergent,
                )
            )
        result = ReconcileResult(rows=rows, divergence_count=divergence_count)
        result.divergence_rate = divergence_count / max(1, len(rows))
        return result
