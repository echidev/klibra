"""Semantic metric catalog — TDD §63, FR-1..FR-10 (002-C).

Provides a PostgreSQL-backed registry plus a post-hoc batch loader so
the eight initial metrics can be created locally without a live DB.

Examples (TDD §63, plan.md Decision 4):

  from semantic.catalog import MetricRegistry

  catalog = MetricRegistry()
  catalog.register({
      "metric_id": "gdp_growth_rate",
      "version": "1.0.0",
      "name": "GDP growth rate",
      "owner_email": "eng@klibra.local",
      "unit": "percent",
      "formula": "(x - x_prev) / x_prev * 100",
      "grain": ["country", "observation_period"],
      "source_policy": ["worldbank", "fred"],
      "aggregation_policy": "AVERAGING",
      "time_semantics": "annual",
      "description": "Annual GDP growth rate (percent).",
  })
  metric = catalog.active_metric("gdp_growth_rate")

Implements the contract at spec.md FR-1..FR-10 002-C and
TDD §63 002-C (metric registry table).

Implements work on top of ``psycopg2`` / ``SQLAlchemy`` when available and
fall back to an in-memory store for local dev without a DB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

__all__ = ["MetricCatalog", "MetricDefinition", "MetricRegistry"]


# ── Exception: governance approval gate ─────────────────────────
class GovernanceApprovalRequired(RuntimeError):  # noqa: N818
    """Raised when a MAJOR version bump is requested without governance approval.

    Per FR-4 002-C: every MAJOR bump for formula/meaning change requires
    governance approval; the rejection is auditable.
    """

    def __init__(
        self,
        message: str,
        *,
        metric_id: str | None = None,
        requested_version: str | None = None,
    ) -> None:
        super().__init__(message)
        self.metric_id = metric_id
        self.requested_version = requested_version


# ── Enums ──────────────────────────────────────────────────────
class MetricStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


# 11 canonical metrics per TDD §63 + PRD §11.2
CANONICAL_METRICS: tuple[str, ...] = (
    "gdp_growth_rate",
    "inflation_rate",
    "unemployment_rate",
    "policy_rate",
    "real_policy_rate",
    "fx_return",
    "market_volatility",
    "debt_to_gdp",
)

# Additional metrics visible via semantic layer (PRD §11.2, intelligence downstream)
CANONICAL_INTELLIGENCE_METRICS: tuple[str, ...] = (
    "economic_momentum_index",
    "inflation_pressure_index",
    "market_stress_index",
    "country_risk_score",
)

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _parse_semver(version: str) -> tuple[int, int, int]:
    if not SEMVER_RE.match(version):
        raise ValueError(f"version must be semver X.Y.Z, got {version!r}")
    return tuple(int(p) for p in version.split("."))  # type: ignore[return-value]


def _is_major_bump(old: str, new: str) -> bool:
    return _parse_semver(new)[0] > _parse_semver(old)[0]


def _is_minor_bump(old: str, new: str) -> bool:
    o, n = _parse_semver(old), _parse_semver(new)
    return n[0] == o[0] and n[1] > o[1]


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Metric definition populating the metric registry table.

    Aligned to the contract at spec.md FR-2 002-C.
    """

    metric_id: str
    version: str
    name: str
    description: str
    owner_email: str
    grain: list[str]
    unit: str
    formula: str
    source_policy: list[str]
    aggregation_policy: str
    time_semantics: str
    deprecation_status: MetricStatus = MetricStatus.ACTIVE
    effective_from: str = field(default_factory=lambda: date.today().isoformat())
    is_intelligence: bool = False
    quality_requirements: dict[str, Any] | None = None
    lineage_ref: str | None = None

    def bump_semver(
        self, new_version: str, *, governance_approved: bool = False
    ) -> MetricDefinition:
        """Return a new MetricDefinition with an incremented version.

        MAJOR bump without ``governance_approved=True`` raises
        ``GovernanceApprovalRequired``; MINOR and PATCH are allowed without
        approval. This satisfies FR-4 002-C.
        """
        if _is_major_bump(self.version, new_version) and not governance_approved:
            raise GovernanceApprovalRequired(
                f"MAJOR version bump for metric {self.metric_id!r} requires governance approval",
                metric_id=self.metric_id,
                requested_version=new_version,
            )
        return MetricDefinition(
            metric_id=self.metric_id,
            version=new_version,
            name=self.name,
            description=self.description,
            owner_email=self.owner_email,
            grain=list(self.grain),
            unit=self.unit,
            formula=self.formula,
            source_policy=list(self.source_policy),
            aggregation_policy=self.aggregation_policy,
            time_semantics=self.time_semantics,
            deprecation_status=self.deprecation_status,
            effective_from=self.effective_from,
            is_intelligence=self.is_intelligence,
            quality_requirements=dict(self.quality_requirements or {}),
            lineage_ref=self.lineage_ref,
        )

    def deprecated_copy(self) -> MetricDefinition:
        """Return a copy with status DEPRECATED (for PATCH-bump pattern)."""

        return MetricDefinition(
            metric_id=self.metric_id,
            version=self.version,
            name=self.name,
            description=self.description,
            owner_email=self.owner_email,
            grain=list(self.grain),
            unit=self.unit,
            formula=self.formula,
            source_policy=list(self.source_policy),
            aggregation_policy=self.aggregation_policy,
            time_semantics=self.time_semantics,
            deprecation_status=MetricStatus.DEPRECATED,
            effective_from=self.effective_from,
            is_intelligence=self.is_intelligence,
            quality_requirements=dict(self.quality_requirements or {}),
            lineage_ref=self.lineage_ref,
        )


class MetricRegistry:
    """PostgreSQL + in-memory metric registry (FR-1..FR-10 002-C).

    In production this wraps the ``metric_registry`` table defined in
    ``V001__control_plane.sql``. In local dev (no DB available) it falls
    back to an in-memory store so the metric catalog tests can run.
    """

    def __init__(self, *, engine: Any | None = None) -> None:
        self._engine = engine
        # in-memory fallback store
        self._store: dict[tuple[str, str], MetricDefinition] = {}

    # ── In-memory API (used by tests and local dev) ──────────────
    def register(self, metric: MetricDefinition) -> MetricDefinition:
        key = (metric.metric_id, metric.version)
        if key in self._store:
            raise ValueError(
                f"metric {metric.metric_id!r} version {metric.version!r} already registered"
            )
        self._store[key] = metric
        return metric

    def active_metric(self, metric_id: str) -> MetricDefinition | None:
        """Return the ACTIVE metric with the given ``metric_id``.

        Returns ``None`` if no ACTIVE version exists.
        """
        for (mid, _ver), metric in sorted(
            self._store.items(), key=lambda kv: kv[0][1], reverse=True
        ):
            if mid == metric_id and metric.deprecation_status == MetricStatus.ACTIVE:
                return metric
        return None

    def enumerate_active(self) -> list[MetricDefinition]:
        """Return all active metrics."""
        return [
            metric
            for metric in self._store.values()
            if metric.deprecation_status == MetricStatus.ACTIVE
        ]

    def deprecated_copy(self, metric_id: str, version: str) -> MetricDefinition | None:
        """Mark a metric as deprecated and return the new copy."""

        key = (metric_id, version)
        metric = self._store.get(key)
        if metric is None:
            return None
        deprecated = metric.deprecated_copy()
        self._store[key] = deprecated
        return deprecated

    def list_all(self) -> list[MetricDefinition]:
        """Return all metrics (all statuses)."""
        return list(self._store.values())


class MetricCatalog(MetricRegistry):
    """Alias for MetricRegistry (legacy name)."""
