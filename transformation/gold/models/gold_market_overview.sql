{{ config(materialized='table') }}

-- Gold: gold_market_overview (002-E)
-- Exposes FX, equity, and commodity indicators aggregated per day
-- for the trailing 252 trading days. PRD §11.1.3, FR-E-2.
-- Combines FX (ECB) and equity (Alpha Vantage) streams via
-- fact_economic_observation (which now ingests both).

with fx as (
    select entity_id, observation_date, value
    from {{ ref('fact_economic_observation') }}
    where metric_id = 'fx_return'
      and effective_to is null
),

equity as (
    select entity_id, observation_date, value
    from {{ ref('fact_economic_observation') }}
    where metric_id = 'gdp_growth_rate'
      and effective_to is null
),

commodity as (
    select entity_id, observation_date, value
    from {{ ref('fact_economic_observation') }}
    where metric_id in ('real_policy_rate', 'market_volatility')
      and effective_to is null
)

select
    'market_overview' as entity_id,
    observation_date,
    avg(fx.value)         as fx_avg,
    avg(equity.value)     as equity_avg,
    avg(commodity.value)  as commodity_avg
from fx
join equity using (observation_date)
join commodity using (observation_date)
group by observation_date
order by observation_date desc
limit 252
