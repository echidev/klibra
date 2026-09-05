-- V002__add_metric_and_intelligence_tables.sql
-- 002-C, 002-D, 002-E, 002-F additive schema.
-- Additive — metric_registry is already in V001__control_plane.sql; this file
-- extends it, and adds fact_intelligence_score + fact_intelligence_component
-- per data-model.md.

BEGIN;

-- ── Metric registry extension (semantic contracts) ───────────
-- V001 already created metric_registry; no additional columns needed.
-- If a column were missing, it would be introduced here.

-- ── Intelligence score tables (TDD §64–§65, Constitution §6.2) ─
CREATE TABLE fact_intelligence_score (
    score_id                UUID PRIMARY KEY,
    metric_id               TEXT NOT NULL,
    entity_id               TEXT NOT NULL,
    observation_period      DATE NOT NULL,
    score                   NUMERIC(8, 4) NOT NULL CHECK (score >= 0 AND score <= 100),
    score_band              TEXT NOT NULL CHECK (score_band IN ('LOW', 'MEDIUM', 'HIGH')),
    confidence              NUMERIC(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    coverage_ratio          NUMERIC(5, 4) NOT NULL CHECK (coverage_ratio >= 0 AND coverage_ratio <= 1),
    methodology_version     TEXT NOT NULL,
    input_snapshot_id       UUID,
    calculated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    quality_status          TEXT NOT NULL DEFAULT 'ACCEPTED'
        CHECK (quality_status IN ('ACCEPTED', 'ACCEPTED_WARNING', 'QUARANTINED', 'REJECTED'))
);

CREATE INDEX idx_fact_intelligence_score_metric ON fact_intelligence_score (metric_id, observation_period DESC);
CREATE INDEX idx_fact_intelligence_score_entity ON fact_intelligence_score (entity_id);

CREATE TABLE fact_intelligence_component (
    score_id                UUID NOT NULL REFERENCES fact_intelligence_score(score_id) ON DELETE CASCADE,
    component_metric_id     TEXT NOT NULL,
    component_value         NUMERIC NOT NULL,
    normalized_value        NUMERIC NOT NULL,
    weight                  NUMERIC(8, 6) NOT NULL CHECK (weight >= 0),
    contribution            NUMERIC NOT NULL,
    quality_status          TEXT NOT NULL CHECK (quality_status IN ('ACCEPTED', 'ACCEPTED_WARNING', 'QUARANTINED')),
    PRIMARY KEY (score_id, component_metric_id)
);

-- Note: weight-sum invariant (sum of weights per score_id = 1.0 within 1e-6)
-- is enforced at the application layer and validated by contract tests; a
-- DB-level constraint on the sum would require a more complex trigger.

INSERT INTO metric_registry (
    metric_id, display_name, description, version, owner_email, grain, unit, formula,
    source_policy, aggregation_policy, time_semantics, lineage_ref,
    effective_from, deprecation_status
) VALUES
 ('gdp_growth_rate', 'GDP growth rate', 'Annual GDP growth rate (percent)', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', '(x - x_prev) / x_prev * 100', '["worldbank", "fred"]', 'AVERAGING', 'annual', NULL, CURRENT_DATE, 'ACTIVE'),
 ('inflation_rate', 'Inflation rate', 'Consumer price inflation (percent)', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', '(cpi - cpi_prev) / cpi_prev * 100', '["worldbank", "fred", "ecb"]', 'AVERAGING', 'monthly', NULL, CURRENT_DATE, 'ACTIVE'),
 ('unemployment_rate', 'Unemployment rate', 'Share of labour force unemployed', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', 'unemployed / labour_force * 100', '["worldbank"]', 'AVERAGING', 'quarterly', NULL, CURRENT_DATE, 'ACTIVE'),
 ('policy_rate', 'Policy rate', 'Central-bank policy rate', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', 'rate', '["fred", "ecb"]', 'LATEST_OBSERVATION', 'monthly', NULL, CURRENT_DATE, 'ACTIVE'),
 ('real_policy_rate', 'Real policy rate', 'Policy rate adjusted for inflation', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', 'policy_rate - inflation_rate', '["fred", "ecb", "worldbank"]', 'AVERAGING', 'monthly', NULL, CURRENT_DATE, 'ACTIVE'),
 ('fx_return', 'FX return', 'Period-over-period FX return', '1.0.0', 'data-platform@klibra.local', '["pair", "observation_period"]', 'percent', '(fx_t / fx_{t-1} - 1) * 100', '["ecb", "alphavantage"]', 'ADDITIVE', 'daily', NULL, CURRENT_DATE, 'ACTIVE'),
 ('market_volatility', 'Market volatility', 'Realized volatility (percent)', '1.0.0', 'data-platform@klibra.local', '["instrument", "observation_period"]', 'percent', 'std(log_return) * sqrt(252)', '["alphavantage", "fred"]', 'AVERAGING', 'daily', NULL, CURRENT_DATE, 'ACTIVE'),
 ('debt_to_gdp', 'Debt to GDP', 'Public debt as share of GDP', '1.0.0', 'data-platform@klibra.local', '["country", "indicator", "observation_period"]', 'percent', 'debt / gdp * 100', '["worldbank"]', 'END_OF_PERIOD', 'annual', NULL, CURRENT_DATE, 'ACTIVE')
ON CONFLICT (metric_id, version) DO NOTHING;

-- ── Alembic version marker (semver; filled by Alembic revision) ─
-- If Alembic is in use, add: INSERT INTO alembic_version (version_num) VALUES ('v002');
COMMIT;
