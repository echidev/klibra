{{ config(materialized='table') }}

select distinct
    dataset_id,
    source_id
from {{ ref('bronze_worldbank_indicators') }}
