{{ config(materialized='incremental', unique_key='observation_id') }}

-- T034 — SCD-2 closure logic
-- TDD §70, Constitution §XIII. Closes the prior version of a fact row when a
-- new version arrives. The prior row receives `effective_to = new.effective_from`,
-- the new row is appended with `effective_to = NULL`.

with new_versions as (
    select * from {{ ref('fact_economic_observation_staging') }}
    where effective_to is null
),

closed as (
    update fact_economic_observation f
    set effective_to = n.effective_from
    from new_versions n
    where f.metric_id = n.metric_id
      and f.entity_id = n.entity_id
      and f.geography_id = n.geography_id
      and coalesce(f.sector_id, '') = coalesce(n.sector_id, '')
      and f.observation_date = n.observation_date
      and f.source_id = n.source_id
      and f.dataset_id = n.dataset_id
      and coalesce(f.source_version, '') = coalesce(n.source_version, '')
      and f.effective_to is null
      and f.effective_from < n.effective_from
    returning f.observation_id
)

insert into fact_economic_observation (
    observation_id, metric_id, entity_id, geography_id, sector_id,
    observation_date, value, unit, source_id, dataset_id,
    publication_date, ingestion_timestamp, effective_from, effective_to,
    source_version, quality_status
)
select
    observation_id, metric_id, entity_id, geography_id, sector_id,
    observation_date, value, unit, source_id, dataset_id,
    publication_date, ingestion_timestamp, effective_from, effective_to,
    source_version, quality_status
from new_versions
where observation_id not in (select observation_id from closed)
