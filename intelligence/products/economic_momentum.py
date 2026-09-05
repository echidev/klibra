"""intelligence_economic_momentum — R3 composite intelligence product.

PRD §11.3, TDD §64.1. Uses GDP growth, employment trend, and an industrial
activity proxy. The methodology is documented in
``intelligence/methodology/economic_momentum.md``.

Weights are version-controlled; weight changes require a MAJOR bump
to ``methodology_version`` (FR-8 002-D).
"""

from __future__ import annotations

from intelligence.composite import CompositeScorer

__all__ = ["EconomicMomentumScorer"]


class EconomicMomentumScorer(CompositeScorer):
    product_id: str = "intelligence_economic_momentum"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {
        "gdp_growth_rate": 0.5,
        "unemployment_rate": 0.3,  # inverse — handled in normalize
        "industrial_activity": 0.2,
    }
    min_coverage: float = 0.66

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        """Map each input to a 0-100 score; unemployment is inverted.

        The simple linear policy: GDP growth → 0-100 over [-10, +10],
        unemployment inversion (lower is better), and pass-through for the
        industrial activity proxy.
        """
        out: dict[str, float] = {}
        if inputs.get("gdp_growth_rate") is not None:
            # Map -10% to 0, +10% to 100, linear clamp
            g = max(-10.0, min(10.0, inputs["gdp_growth_rate"]))
            out["gdp_growth_rate"] = (g + 10.0) * 5.0
        if inputs.get("unemployment_rate") is not None:
            # Lower unemployment = higher contribution
            u = max(0.0, min(30.0, inputs["unemployment_rate"]))
            out["unemployment_rate"] = (30.0 - u) * (100.0 / 30.0)
        if inputs.get("industrial_activity") is not None:
            out["industrial_activity"] = max(0.0, min(100.0, inputs["industrial_activity"]))
        return out
