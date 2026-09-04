{{ config(materialized='table', post_hook='analyze table gold_macro_indicators compute statistics') }}

-- Gold: gold_macro_indicators
-- TDD §10 — consumer-oriented curated product.
-- Depends on fact_economic_observation (Silver).

with silver as (
    select
        observation_id,
        metric_id,
        entity_id,
        geography_id,
        sector_id,
        observation_date,
        value,
        unit,
        source_id,
        dataset_id,
        publication_date,
        ingestion_timestamp,
        effective_from,
        effective_to,
        quality_status,
        run_id,
        payload_hash
    from {{ ref('fact_economic_observation') }}
    where effective_to is null
      and quality_status in ('ACCEPTED', 'ACCEPTED_WARNING')
),

gold as (
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
        'https://raw.github.klibra/fact_economic_observation/' || observation_id as lineage_ref
    from silver
)

select * from gold
