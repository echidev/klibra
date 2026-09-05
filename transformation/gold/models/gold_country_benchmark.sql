{{ config(materialized='table') }}

-- Gold: gold_country_benchmark (002-E)
-- Pivots Silver fact_economic_observation per entity_id with a fixed
-- metric basket (gdp_growth_rate, inflation_rate, unemployment_rate,
-- debt_to_gdp). TDD §9.

with silver as (
    select
        entity_id,
        metric_id,
        observation_date,
        value,
        unit,
        source_id,
        dataset_id,
        run_id,
        payload_hash,
        effective_from
    from {{ ref('fact_economic_observation') }}
    where effective_to is null
      and metric_id in ('gdp_growth_rate', 'inflation_rate', 'unemployment_rate', 'debt_to_gdp')
      and value is not null
    -- Latest per (entity_id, metric_id) at the maximum effective_from
    qualify row_number() over (
        partition by entity_id, metric_id
        order by effective_from desc
    ) = 1
)

pivoted as (
    select
        entity_id,
        max(case when metric_id = 'gdp_growth_rate'      then value end) as gdp_growth_rate,
        max(case when metric_id = 'inflation_rate'       then value end) as inflation_rate,
        max(case when metric_id = 'unemployment_rate'    then value end) as unemployment_rate,
        max(case when metric_id = 'debt_to_gdp'          then value end) as debt_to_gdp
    from silver
    group by entity_id
)

select
    p.entity_id,
    p.gdp_growth_rate,
    p.inflation_rate,
    p.unemployment_rate,
    p.debt_to_gdp,
    'percent' as unit,
    now() as gold_published_at
from pivoted p
