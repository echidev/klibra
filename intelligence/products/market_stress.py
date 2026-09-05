"""intelligence_market_stress — R3 composite intelligence product.

PRD §11.3, TDD §64.3. Uses equity volatility, FX volatility, and a
yield-spread proxy. Methodology in
``intelligence/methodology/market_stress.md``.

Golden file for FR-7 002-D and the user scenario at spec.md §002-D
Scenario 4 (Risk Analyst).
"""

from __future__ import annotations

from intelligence.composite import CompositeScorer

__all__ = ["MarketStressScorer"]


class MarketStressScorer(CompositeScorer):
    product_id: str = "intelligence_market_stress"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {
        "market_volatility": 0.5,
        "fx_volatility": 0.3,
        "yield_spread_proxy": 0.2,
    }
    min_coverage: float = 0.66

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        # Volatility inputs are typically 0-100; cap and pass through.
        if inputs.get("market_volatility") is not None:
            out["market_volatility"] = max(0.0, min(100.0, inputs["market_volatility"]))
        if inputs.get("fx_volatility") is not None:
            out["fx_volatility"] = max(0.0, min(100.0, inputs["fx_volatility"]))
        if inputs.get("yield_spread_proxy") is not None:
            # Inverted: tight spread = stress; wide = calm
            # Map 0-500 bp to 100-0
            y = max(0.0, min(500.0, inputs["yield_spread_proxy"]))
            out["yield_spread_proxy"] = max(0.0, min(100.0, 100.0 - (y / 5.0)))
        return out
