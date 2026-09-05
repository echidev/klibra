"""intelligence_global_liquidity — R3 composite intelligence product.

PRD §11.3. Combines global FX return, real policy rate, and market
volatility into a single liquidity stress score. Methodology in
``intelligence/methodology/global_liquidity.md``.
"""

from __future__ import annotations

from intelligence.composite import CompositeScorer

__all__ = ["GlobalLiquidityScorer"]


class GlobalLiquidityScorer(CompositeScorer):
    product_id: str = "intelligence_global_liquidity"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {
        "fx_return": 0.4,
        "real_policy_rate": 0.4,
        "market_volatility": 0.2,
    }
    min_coverage: float = 0.66

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        # fx_return: large absolute returns indicate stress
        if inputs.get("fx_return") is not None:
            r = abs(inputs["fx_return"])
            out["fx_return"] = max(0.0, min(100.0, r * 5.0))
        # real_policy_rate: very low = accommodative; very high = restrictive
        if inputs.get("real_policy_rate") is not None:
            r = inputs["real_policy_rate"]
            # Map -5% to 100, +5% to 0
            rr = max(-5.0, min(5.0, r))
            out["real_policy_rate"] = (5.0 - rr) * 10.0
        if inputs.get("market_volatility") is not None:
            out["market_volatility"] = max(0.0, min(100.0, inputs["market_volatility"]))
        return out
