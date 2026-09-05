{{ config(materialized='table') }}

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
from {{ ref('bronze_worldbank_seed') }}
