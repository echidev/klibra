{{ config(materialized='table') }}

with source_rows as (
    select *
    from {{ ref('bronze_worldbank_indicators') }}
),

mapped as (
    select
        md5(
            source_id || '|' || dataset_id || '|' || country_id || '|' ||
            indicator_id || '|' || observation_date || '|' || payload_hash
        ) as observation_id,
        case indicator_id
            when 'NY.GDP.MKTP.KD.ZG' then 'gdp_growth_rate'
            when 'FP.CPI.TOTL.ZG' then 'inflation_rate'
            when 'SL.UEM.TOTL.ZS' then 'unemployment_rate'
            when 'FR.INR.RINR' then 'real_policy_rate'
            else lower(regexp_replace(indicator_id, '\\.', '_', 'g'))
        end as metric_id,
        country_id as entity_id,
        country_id as geography_id,
        case
            when indicator_id like 'NY.GDP%' then 'gdp'
            when indicator_id like 'FP.CPI%' then 'inflation'
            when indicator_id like 'SL.UEM%' then 'employment'
            else 'unknown'
        end as sector_id,
        cast(observation_date || '-01-01' as date) as observation_date,
        cast(value as double) as value,
        coalesce(unit, '') as unit,
        source_id,
        dataset_id,
        cast(null as date) as publication_date,
        cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
        cast(ingestion_timestamp as timestamp) as effective_from,
        cast(null as timestamp) as effective_to,
        cast(null as varchar) as source_version,
        'ACCEPTED' as quality_status,
        ingestion_run_id as run_id,
        payload_hash
    from source_rows
    where indicator_id is not null
      and observation_date is not null
      and value is not null
)

select * from mapped
