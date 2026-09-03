# KLIBRA — Lineage Policy

**Document Type:** Lineage Policy  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §13 (scope), §30 (metadata); TDD §28, §59, §61, §65, §66, §71  

---

## 1. Purpose

Define standards for capturing, maintaining, and auditing data lineage across all layers of the KLIBRA platform (TDD §28, ADR‑008).

---

## 2. Scope

Applies to all data movement and transformation:

- Raw ingestion → Bronze → Silver → Gold → Semantic → Intelligence products.
- Metadata propagation (pipeline run IDs, payload hashes, source versions).
- Backfills and schema‑drift handling.

---

## 3. Lineage Requirements

Every dataset must store:

- **Source metadata:** `source_id`, `dataset_id`, `source_version`, `payload_hash`, retrieval timestamps.
- **Transformation lineage:** For each stage, the code version and run_id that produced the record.
- **Temporal lineage:** Observation, publication, ingestion, effective‑from/to timestamps (ADR‑007).
- **Contract lineage:** Reference to the active data contract version.

Lineage must be available at:

- **Dataset level** for all datasets (mandatory).
- **Field level** where practical, especially for semantic metrics and intelligence products (TDD §28).

---

## 4. Lineage Capture Mechanism

- Lineage records emitted as structured JSON (`manifest.json`) stored in the `metadata/` layer alongside raw objects and in the metadata database.
- **OpenMetadata** is the primary catalog for lineage visualization (PRD §30, TDD §68‑§69).
- **dbt** provides lineage for SQL‑based transformations (TDD §24).
- **Airflow** DAG metadata links runs to lineage (ADR‑004).

---

## 5. Lineage Verification

- Automated lineage checks are part of the CI/CD pipeline (TDD §79): contract tests verify that source → Gold lineage records exist.
- Production deployment blocked if lineage coverage falls below **100 %** for production datasets (PRD §32.4).

---

## 6. Lineage Retention

Lineage records retained for **≥5 years** (or per dataset retention policy).

---

## 7. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — FINDEX lineage |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Updated to KLIBRA PRD v2.0 / TDD v2.0; clarified dataset vs. field‑level requirements, aligned with effective‑from/to & intake provenance |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
