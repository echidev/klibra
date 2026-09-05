{{ config(materialized='table') }}

-- Gold: gold_market_overview (003, FR-14)
-- Per-day FX, equity, and commodity indicators for the most recent 252
-- trading days. FULL OUTER JOIN by `observation_date` so missing instrument
-- days are NULL rather than dropped. Filter by `dim_calendar.is_trading_day`.

with silver as (
    select observation_date, source_id, metric_id, value
    from {{ ref('fact_economic_observation') }}
    where effective_to is null
      and metric_id in ('fx_return', 'market_volatility', 'real_policy_rate')
),

fx as (
    select observation_date, value as fx_value
    from silver
    where metric_id = 'fx_return'
),

equity as (
    select observation_date, value as equity_value
    from silver
    where metric_id = 'market_volatility'
    and source_id in ('alphavantage', 'fred')
),

commodity as (
    select observation_date, value as commodity_value
    from silver
    where metric_id = 'real_policy_rate'
    and source_id = 'ecb'
),

joined as (
    select
        coalesce(fx.observation_date, equity.observation_date, commodity.observation_date) as observation_date,
        fx.fx_value,
        equity.equity_value,
        commodity.commodity_value
    from fx
    full outer join equity using (observation_date)
    full outer join commodity using (observation_date)
)

select
    observation_date,
    avg(fx_value) as fx_avg,
    avg(equity_value) as equity_avg,
    avg(commodity_value) as commodity_avg,
    cast(ceil(epoch(now() - cast(observation_date as timestamp)) / 3600) as bigint) as freshness_hours
from joined
inner join {{ ref('dim_calendar') }} dim
    on dim.date = joined.observation_date
    and dim.is_trading_day = true
group by observation_date
order by observation_date desc
limit 252
