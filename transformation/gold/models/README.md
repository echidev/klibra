# Gold Macro Indicators — Documentation & Lineage Narrative

## Purpose

`gold_macro_indicators` provides the primary curated dataset for macroeconomic
indicators (GDP growth, inflation, unemployment) across countries. It is
consumer-facing and optimized for analyst consumption (TDD §10).

## Data Model

| Field | Type | Description |
|---|---|---|
| `metric_id` | string | Standardized metric identifier |
| `entity_id` | string | Country or region identifier |
| `geography_id` | string | Geography dimension FK |
| `observation_date` | date | Period the value refers to |
| `value` | decimal | Observation value |
| `unit` | string | Unit of measure (post-standardization) |
| `source_id` | string | Registered source ID |
| `dataset_id` | string | Registered dataset ID |
| `effective_from` | timestamp | SCD-2 start timestamp |
| `run_id` | string | Pipeline run ID |
| `payload_hash` | string | SHA-256 of original source payload |
| `lineage_ref` | string | URL to Silver fact for lineage tracing |

## Lineage

```text
World Bank Indicators API
  ↓ extract (connector)
Raw payload (sha256)
  ↓ bronze transform
bronze_worldbank_indicators
  ↓ silver standardization
fact_economic_observation
  ↓ gold curation
gold_macro_indicators
```

Field-level lineage:
- `metric_id` ← `indicator_id` (World Bank V2 API)
- `entity_id` ← `country_id` (World Bank V2 API)
- `value` ← `value` (World Bank V2 API)
- `observation_date` ← `date` (World Bank V2 API)
- `unit` ← `unit` (World Bank V2 API)

## Known Limitations

- Values are null when the source provides no observation for a period.
- Gold reflects only current records (`effective_to IS NULL`); for
  point-in-time queries use the Silver layer directly.
- Unit standardization is applied per metric; some indicators do not
  specify a unit in the source payload.

## Refresh Schedule

- Cadence: Monthly (aligned with World Bank publication schedule).
- Freshness SLO: ≤ 720 hours between expected publications.
- Failure behavior: Quarantine and alert per quality governance.
