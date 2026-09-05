"""intelligence_inflation_pressure — R3 composite intelligence product.

PRD §11.3, TDD §64.2. Uses inflation trend, a producer-price proxy,
and policy rate / real-rate context. Methodology in
``intelligence/methodology/inflation_pressure.md``.
"""

from __future__ import annotations

from intelligence.composite import CompositeScorer

__all__ = ["InflationPressureScorer"]


class InflationPressureScorer(CompositeScorer):
    product_id: str = "intelligence_inflation_pressure"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {
        "inflation_rate": 0.5,
        "producer_price": 0.3,
        "real_policy_rate": 0.2,
    }
    min_coverage: float = 0.66

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        if inputs.get("inflation_rate") is not None:
            # Higher inflation → higher pressure
            i = max(-5.0, min(20.0, inputs["inflation_rate"]))
            out["inflation_rate"] = max(0.0, min(100.0, (i + 5.0) * 4.0))
        if inputs.get("producer_price") is not None:
            pp = max(-5.0, min(20.0, inputs["producer_price"]))
            out["producer_price"] = max(0.0, min(100.0, (pp + 5.0) * 4.0))
        if inputs.get("real_policy_rate") is not None:
            r = inputs["real_policy_rate"]
            # Real rate < 0 → accommodative → higher pressure; > 0 → restrictive
            # Map -5% to 100, +5% to 0
            rr = max(-5.0, min(5.0, r))
            out["real_policy_rate"] = (5.0 - rr) * 10.0
        return out
