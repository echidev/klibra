{{ config(materialized='table') }}

-- Bronze: FRED (003, FR-9, gap G5)
-- Mirrors transformation/bronze/fred.py; two-call pattern (series metadata
-- + observations) flattened into one Bronze table row per observation.

select
    source_id,
    dataset_id,
    metric_id,
    run_id,
    ingestion_timestamp,
    payload_hash,
    raw_source_url,
    frequency,
    title,
    units,
    seasonal_adjustment,
    observation_date,
    value,
    realtime_start,
    realtime_end
from {{ ref('bronze_fred_seed') }}
