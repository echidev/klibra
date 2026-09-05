{{ config(materialized='table') }}

-- Bronze: ECB SDMX (003, FR-9, gap G5)
-- Mirrors transformation/bronze/ecb_indicators.py; maps SDMX csvdata
-- (FREQ, CURRENCY, CURRENCY_DENOM, EXR_TYPE, EXR_SUFFIX,
--  TIME_PERIOD, OBS_VALUE) into bronze columns. In dbt we expose it as
-- a thin select from the existing bronze_ecb_seed (or a view when
-- the in-Python parser is the authoritative Bronze stage).

select
    source_id,
    dataset_id,
    run_id,
    ingestion_timestamp,
    payload_hash,
    raw_source_url,
    frequency,
    currency,
    currency_denom,
    exr_type,
    exr_suffix,
    observation_date,
    value,
    unit,
    obs_status,
    title
from {{ ref('bronze_ecb_seed') }}
