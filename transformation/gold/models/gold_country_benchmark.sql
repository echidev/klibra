{{ config(materialized='table') }}

-- Gold: gold_country_benchmark (003, FR-13)
-- DuckDB-compatible (no `qualify` syntax): pivot latest per (entity, metric)
-- from silver union (worldbank + ecb + fred + alphavantage), fixed metric
-- basket (gdp_growth_rate, inflation_rate, unemployment_rate, debt_to_gdp).
-- Adds freshness_hours per spec FR-E-1.
-- SCD2 invariant: ``effective_to is null`` marks open versions; latest per
-- (entity, metric) is chosen by ``row_number() over (... order by
-- effective_from desc)`` so the most recent valid day wins.

with latest as (
    select *
    from (
        select
            entity_id,
            metric_id,
            observation_date,
            value,
            row_number() over (
                partition by entity_id, metric_id
                order by effective_from desc, observation_date desc, run_id desc
            ) as rn
        from {{ ref('fact_economic_observation') }}
        where effective_to is null
          and quality_status in ('ACCEPTED', 'ACCEPTED_WARNING')
          and metric_id in ('gdp_growth_rate', 'inflation_rate', 'unemployment_rate', 'debt_to_gdp')
    ) sub
    where rn = 1
),

pivoted as (
    select
        entity_id,
        max(case when metric_id = 'gdp_growth_rate' then value end) as gdp_growth_rate,
        max(case when metric_id = 'inflation_rate' then value end) as inflation_rate,
        max(case when metric_id = 'unemployment_rate' then value end) as unemployment_rate,
        max(case when metric_id = 'debt_to_gdp' then value end) as debt_to_gdp,
        max(observation_date) as latest_observation_date
    from latest
    group by entity_id
)

select
    entity_id,
    gdp_growth_rate,
    inflation_rate,
    unemployment_rate,
    debt_to_gdp,
    'percent' as unit,
    cast(ceil(epoch(now() - cast(latest_observation_date as timestamp)) / 3600) as bigint) as freshness_hours,
    now() as gold_published_at
from pivoted
