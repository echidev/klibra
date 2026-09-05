"""Unit tests for the semantic metric registry.

Covers FR-1..FR-10 of spec.md §002-C and SC-C-1..SC-C-5.
"""

from __future__ import annotations

import pytest

from semantic.catalog import (
    GovernanceApprovalRequired,
    MetricDefinition,
    MetricRegistry,
    MetricStatus,
)


def _make_metric(metric_id: str = "gdp_growth_rate", version: str = "1.0.0") -> MetricDefinition:
    return MetricDefinition(
        metric_id=metric_id,
        version=version,
        name="GDP growth rate",
        description="Annual GDP growth rate (percent).",
        owner_email="eng@klibra.local",
        grain=["country", "observation_period"],
        unit="percent",
        formula="(x - x_prev) / x_prev * 100",
        source_policy=["worldbank", "fred"],
        aggregation_policy="AVERAGING",
        time_semantics="annual",
    )


def test_register_and_active_lookup() -> None:
    catalog = MetricRegistry()
    m = _make_metric()
    catalog.register(m)
    assert catalog.active_metric("gdp_growth_rate") is not None
    assert catalog.active_metric("gdp_growth_rate").version == "1.0.0"


def test_duplicate_rejection() -> None:
    catalog = MetricRegistry()
    m = _make_metric()
    catalog.register(m)
    with pytest.raises(ValueError, match="already registered"):
        catalog.register(m)


def test_patch_deprecated_marking() -> None:
    catalog = MetricRegistry()
    m = _make_metric(version="1.0.0")
    catalog.register(m)
    deprecated = catalog.deprecated_copy("gdp_growth_rate", "1.0.0")
    assert deprecated is not None
    assert deprecated.deprecation_status == MetricStatus.DEPRECATED
    # Deprecated metric is no longer active
    assert catalog.active_metric("gdp_growth_rate") is None


def test_major_governance_guard() -> None:
    catalog = MetricRegistry()
    m = _make_metric(version="1.0.0")
    catalog.register(m)
    # MAJOR bump without governance approval must raise
    with pytest.raises(GovernanceApprovalRequired):
        m.bump_semver("2.0.0", governance_approved=False)
    # With governance approval it succeeds
    m2 = m.bump_semver("2.0.0", governance_approved=True)
    assert m2.version == "2.0.0"


def test_active_lookup_returns_none_for_unknown() -> None:
    catalog = MetricRegistry()
    assert catalog.active_metric("nonexistent_metric") is None


def test_enumerate_active() -> None:
    catalog = MetricRegistry()
    m1 = _make_metric(metric_id="gdp_growth_rate", version="1.0.0")
    m2 = _make_metric(metric_id="inflation_rate", version="1.0.0")
    catalog.register(m1)
    catalog.register(m2)
    active = catalog.enumerate_active()
    assert len(active) == 2
    assert {m.metric_id for m in active} == {"gdp_growth_rate", "inflation_rate"}


def test_bump_semver_without_governance_raises() -> None:
    m = _make_metric(version="1.5.0")
    with pytest.raises(GovernanceApprovalRequired, match="governance approval"):
        m.bump_semver("2.0.0", governance_approved=False)


def test_bump_semver_with_governance_succeeds() -> None:
    m = _make_metric(version="1.5.0")
    m2 = m.bump_semver("2.0.0", governance_approved=True)
    assert m2.version == "2.0.0"
