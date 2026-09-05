"""Explicit source-series to governed semantic metric mappings."""

from __future__ import annotations

__all__ = ["semantic_metric_id"]

_SOURCE_METRIC_MAP: dict[tuple[str, str], str] = {
    ("worldbank", "NY.GDP.MKTP.KD.ZG"): "gdp_growth_rate",
    ("worldbank", "FP.CPI.TOTL.ZG"): "inflation_rate",
    ("worldbank", "SL.UEM.TOTL.ZS"): "unemployment_rate",
    ("worldbank", "FR.INR.RINR"): "real_policy_rate",
    ("fred", "GDPC1"): "gdp_growth_rate",
    ("fred", "FEDFUNDS"): "policy_rate",
    ("fred", "DEXUSEU"): "fx_return",
    ("ecb", "EXR.D.USD.EUR.SP00.A"): "fx_return",
    ("ecb", "EXR.M.USD.EUR.SP00.A"): "fx_return",
}


def semantic_metric_id(source_id: str, source_series_id: str) -> str:
    """Resolve a source series to its governed metric, with explicit fallback."""
    return _SOURCE_METRIC_MAP.get(
        (source_id, source_series_id), source_series_id.lower().replace(".", "_")
    )
