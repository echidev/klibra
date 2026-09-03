# KLIBRA — Glossary

**Document Type:** Glossary  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §5 (business terms), §27 (semantic metrics), §28 (intelligence); TDD §63 (metric registry), §65 (intelligence score model)  

---

## 1. Purpose

Provide authoritative definitions for key terms used throughout KLIBRA documentation, pipelines, contracts, and stakeholder communication. Ensures consistent understanding across teams (PRD §5, TDD §33).

---

## 2. Glossary Entries

| Term | Definition |
| --- | --- |
| **Observation Time** | The point in time the economic event or measurement refers to (e.g., a month’s GDP figure). |
| **Publication Time** | The timestamp when a source publishes the observation (may differ from observation time). |
| **Ingestion Time** | The timestamp when KLIBRA ingests the payload into the Raw layer. |
| **Effective From / To** | Temporal bounds indicating when a particular version of a record is authoritative (SCD‑2 semantics). |
| **Metric** | A quantitative measurement defined in the semantic layer (e.g., `gdp_growth_rate`). |
| **Grain** | The dimensionality of a metric, expressed as a tuple (e.g., `(country, indicator, observation_period)`). |
| **Semantic Metric** | A governed business metric defined in the semantic layer, with formula, version, and lineage. |
| **Intelligence Product** | A composite score derived from multiple semantic metrics (e.g., `intelligence_market_stress`). |
| **Source Catalog** | Registry of approved public data sources, access class, and endpoint details (PRD §10.1). |
| **Access Class** | Classification of source access requirements: **A** – no key, **B** – self‑service key, **C** – portal/account required (PRD §10.1). |
| **Idempotency Key** | Deterministic identifier ensuring exactly‑once ingestion (source_id, dataset_id, period, version, payload_hash). |
| **Quarantine** | Layer for records that failed blocking quality checks; isolated for investigation. |
| **Gold Layer** | Consumer‑oriented data products ready for downstream consumption. |
| **Bronze Layer** | Source‑aligned, minimally transformed representation preserving original fields. |
| **Silver Layer** | Standardized, validated dataset conforming to the canonical model. |
| **Lineage** | End‑to‑end traceability from Gold product back to the original source payload. |
| **Backfill** | Explicit re‑processing of historical periods to correct or augment data (Runbook‑Backfill). |
| **Schema Drift** | Unplanned changes in source schema that may affect pipelines (TDD §19). |
| **P0 / P1 / P2 / P3** | Quality severity levels defined in TDD §22 and used throughout the platform. |
| **ADR** | Architecture Decision Record – captured design decisions (see `docs/architecture/decisions/`). |
| **SLA** | Service Level Agreement – e.g., freshness SLA (99% of scheduled runs). |
| **RPO / RTO** | Recovery Point Objective / Recovery Time Objective (Disaster Recovery). |
| **Data Contract** | Formal specification of dataset schema, quality thresholds, retention, and lineage (PRD §29, TDD §66). |
| **Metric Grain** | The set of dimensions that uniquely identify a metric observation. |
| **Temporal Semantics** | Rules for handling observation vs. publication vs. ingestion timestamps. |
| **Effective Date** | The date when a data product version becomes active for consumers. |
| **Versioning** | Semantic versioning applied to metrics, contracts, and intelligence methodologies. |
| **Backfill Run ID** | Unique identifier for a backfill execution, recorded in ingestion metadata. |
| **Connector Interface** | Standard set of functions for source connectors (ADR‑002). |
| **Airflow DAG** | Directed acyclic graph defining the execution order of pipeline stages (ADR‑004). |
| **AWS S3 Lifecycle Policy** | Automated transition of objects between storage classes (ADR‑008). |
| **Data Steward** | Individual responsible for data quality and documentation for a specific domain. |
| **Business Consumer** | End‑user or downstream system that consumes Gold products or semantic metrics. |

---

## 3. Maintenance

- Glossary entries are stored in this markdown file and version‑controlled.
- New terms added via pull request; must include definition and cross‑reference to PRD/TDD.
- Quarterly review by Data Governance Committee.

---

## 4. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — FINDEX glossary |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Updated for KLIBRA PRD v2.0 / TDD v2.0; added KLIBRA‑specific terms and aligned definitions |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
