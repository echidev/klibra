{{ config(materialized='table', post_hook='analyze table fact_economic_observation compute statistics') }}

-- Silver: fact_economic_observation
-- TDD §9, §11 — canonical fact plus dimension joins.
-- Depends on bronze_worldbank_indicators (from T020).

with bronze as (
    select
        source_id,
        dataset_id,
        country_id,
        country_iso3,
        country_name,
        indicator_id,
        indicator_name,
        observation_date,
        value,
        unit,
        obs_status,
        decimal,
        ingestion_run_id,
        ingestion_timestamp,
        payload_hash,
        raw_source_url
    from {{ ref('bronze_worldbank_indicators') }}
),

mapped as (
    select
        md5(
            indicator_id || '-' || coalesce(country_id, 'unknown') || '-' || coalesce(observation_date, 'unknown')
        ) as observation_id,
        lower(regexp_replace(indicator_id, '\.', '_', 'g')) as metric_id,
        country_id as entity_id,
        country_id as geography_id,
        case
            when indicator_id ilike 'NY.GDP%' then 'gdp'
            when indicator_id ilike 'FP.CPI%' then 'inflation'
            when indicator_id ilike 'SL.UEM%' then 'employment'
            else 'unknown'
        end as sector_id,
        cast(observation_date as date) as observation_date,
        cast(value as double) as value,
        coalesce(unit, '') as unit,
        source_id,
        dataset_id,
        null::date as publication_date,
        cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
        cast(ingestion_timestamp as timestamp) as effective_from,
        null::timestamp as effective_to,
        null::varchar as source_version,
        'ACCEPTED' as quality_status,
        ingestion_run_id as run_id,
        payload_hash
    from bronze
    where indicator_id is not null
      and observation_date is not null
      and value is not null
)

select * from mapped
