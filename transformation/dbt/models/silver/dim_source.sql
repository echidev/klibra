{{ config(materialized='table') }}

select distinct
    source_id,
    source_id as source_name
from {{ ref('bronze_worldbank_indicators') }}
