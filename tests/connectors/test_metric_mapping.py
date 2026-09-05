"""Contract tests for explicit source-to-semantic metric mappings."""

from ingestion.util.metric_mapping import semantic_metric_id


def test_known_source_series_maps_to_governed_metric() -> None:
    assert semantic_metric_id("worldbank", "NY.GDP.MKTP.KD.ZG") == "gdp_growth_rate"
    assert semantic_metric_id("fred", "FEDFUNDS") == "policy_rate"
    assert semantic_metric_id("ecb", "EXR.D.USD.EUR.SP00.A") == "fx_return"


def test_unknown_source_series_has_stable_fallback() -> None:
    assert semantic_metric_id("fred", "CUSTOM.SERIES") == "custom_series"
