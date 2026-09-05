"""intelligence_country_risk — R3 composite intelligence product.

PRD §11.3. Combines policy rate, inflation, debt-to-GDP, and current-account
stress into a single risk score (0-100, higher is riskier). Methodology in
``intelligence/methodology/country_risk.md``.
"""

from __future__ import annotations

from intelligence.composite import CompositeScorer

__all__ = ["CountryRiskScorer"]


class CountryRiskScorer(CompositeScorer):
    product_id: str = "intelligence_country_risk"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {
        "policy_rate": 0.3,
        "inflation_rate": 0.3,
        "debt_to_gdp": 0.3,
        "current_account_stress": 0.1,
    }
    min_coverage: float = 0.5

    def normalize(self, inputs: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        # policy_rate: high rates reduce risk → invert
        if inputs.get("policy_rate") is not None:
            r = max(0.0, min(20.0, inputs["policy_rate"]))
            out["policy_rate"] = max(0.0, min(100.0, 100.0 - r * 5.0))
        if inputs.get("inflation_rate") is not None:
            i = max(-5.0, min(20.0, inputs["inflation_rate"]))
            out["inflation_rate"] = max(0.0, min(100.0, (i + 5.0) * 4.0))
        if inputs.get("debt_to_gdp") is not None:
            d = max(0.0, min(200.0, inputs["debt_to_gdp"]))
            out["debt_to_gdp"] = max(0.0, min(100.0, d * 0.5))
        if inputs.get("current_account_stress") is not None:
            out["current_account_stress"] = max(0.0, min(100.0, inputs["current_account_stress"]))
        return out
