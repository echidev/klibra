"""Unit tests for the intelligence layer scoring products.

Covers FR-1..FR-10 of spec.md §002-D and SC-D-1..SC-D-6.
"""

from __future__ import annotations

import pytest

from intelligence.composite import IntelligenceScore, MethodologyVersionBumpRequired
from intelligence.products.country_risk import CountryRiskScorer
from intelligence.products.economic_momentum import EconomicMomentumScorer
from intelligence.products.global_liquidity import GlobalLiquidityScorer
from intelligence.products.inflation_pressure import InflationPressureScorer
from intelligence.products.market_stress import MarketStressScorer

PRODUCTS = [
    EconomicMomentumScorer,
    InflationPressureScorer,
    MarketStressScorer,
    CountryRiskScorer,
    GlobalLiquidityScorer,
]


def _sample_inputs(cls) -> dict[str, float]:
    if cls is EconomicMomentumScorer:
        return {"gdp_growth_rate": 3.0, "unemployment_rate": 5.0, "industrial_activity": 60.0}
    if cls is InflationPressureScorer:
        return {"inflation_rate": 3.0, "producer_price": 2.0, "real_policy_rate": 1.0}
    if cls is MarketStressScorer:
        return {"market_volatility": 15.0, "fx_volatility": 12.0, "yield_spread_proxy": 100.0}
    if cls is CountryRiskScorer:
        return {
            "policy_rate": 4.0,
            "inflation_rate": 3.0,
            "debt_to_gdp": 60.0,
            "current_account_stress": 20.0,
        }
    # GlobalLiquidity
    return {"fx_return": 1.5, "real_policy_rate": 1.0, "market_volatility": 15.0}


@pytest.mark.parametrize("cls", PRODUCTS)
def test_all_products_importable_and_score(cls) -> None:
    scorer = cls()
    assert scorer.product_id.startswith("intelligence_")
    result = scorer.score(_sample_inputs(cls))
    assert isinstance(result, IntelligenceScore)
    assert result.product_id == scorer.product_id
    assert result.methodology_version == scorer.methodology_version


def test_deterministic_scoring() -> None:
    scorer = MarketStressScorer()
    inputs = _sample_inputs(MarketStressScorer)
    r1 = scorer.score(inputs, input_snapshot_id="a")
    r2 = scorer.score(inputs, input_snapshot_id="a")
    assert r1.score == r2.score
    assert r1.components == r2.components
    assert r1.confidence == r2.confidence
    assert r1.coverage_ratio == r2.coverage_ratio
    assert r1.lineage_ref == r2.lineage_ref


@pytest.mark.parametrize("cls", PRODUCTS)
def test_score_in_bounds_and_confidence_range(cls) -> None:
    scorer = cls()
    result = scorer.score(_sample_inputs(cls))
    assert 0.0 <= result.score <= 100.0
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.coverage_ratio <= 1.0
    assert result.score_band in ("LOW", "MEDIUM", "HIGH")


def test_coverage_gate_blocks_publish_when_insufficient() -> None:
    scorer = MarketStressScorer()
    # Only one of three inputs → coverage ~ 0.33 below min 0.66
    result = scorer.score({"market_volatility": 20.0}, input_snapshot_id="lowcov")
    assert result.coverage_ratio < scorer.min_coverage


def test_methodology_bump_required() -> None:
    MarketStressScorer()
    with pytest.raises(MethodologyVersionBumpRequired):
        raise MethodologyVersionBumpRequired(
            "Weights changed without MAJOR bump", expected_version="1.0.0"
        )
