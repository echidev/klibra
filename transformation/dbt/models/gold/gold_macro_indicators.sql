{{ config(materialized='table') }}

select
    metric_id,
    entity_id,
    geography_id,
    observation_date,
    value,
    unit,
    source_id,
    dataset_id,
    effective_from as gold_from,
    run_id,
    payload_hash,
    'silver.fact_economic_observation:' || observation_id as lineage_ref
from {{ ref('fact_economic_observation') }}
where effective_to is null
  and quality_status in ('ACCEPTED', 'ACCEPTED_WARNING')
