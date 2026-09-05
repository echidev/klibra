{{ config(materialized='table') }}

-- Bronze: Alpha Vantage (003, FR-7/FR-9, gap G3/G5)
-- Mirrors transformation/bronze/alphavantage.py; GLOBAL_QUOTE /
-- TIME_SERIES_DAILY normalized to: source_id, dataset_id, instrument_id,
-- observation_date (date), value (double), unit (price), title.

select
    source_id,
    dataset_id,
    instrument_id,
    observation_date,
    value,
    unit,
    title,
    frequency,
    country_id,
    indicator_id,
    run_id,
    ingestion_timestamp,
    payload_hash,
    raw_source_url
from {{ ref('bronze_alphavantage_seed') }}
