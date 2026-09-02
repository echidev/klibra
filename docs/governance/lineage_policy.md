# FINDEX — Lineage Policy

**Document Type:** Lineage Policy  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Governance Team  
**Classification:** Internal  

---

## 1. Purpose

This Lineage Policy establishes standards for data lineage across the FINDEX platform. Lineage provides the ability to trace any data value from its consumption point back through all processing stages to its original source.

Lineage ensures:
- Traceability from curated data to source data
- Impact analysis when sources change
- Reproducibility of analytical results
- Auditability of data transformations
- Consumer confidence in data origins

---

## 2. Scope

This policy applies to all data movement and transformation within the FINDEX platform:

- Source → Raw preservation
- Raw → Bronze transformation
- Bronze → Silver standardization
- Silver → Gold business modeling
- Gold → Consumer delivery (Athena, BI, API)

Lineage covers both dataset-level and field-level traceability.

---

## 3. Lineage Standards

### 3.1 Lineage Levels

| Level | Description | Requirement |
|---|---|---|
| **Dataset Level** | Trace which source dataset produced which downstream dataset | **Mandatory** for all production datasets |
| **Field Level** | Trace individual field transformations from source to consumer | Required where practical |
| **Record Level** | Trace individual record processing (hash, row_id) | Supported via `row_hash` and `observation_id` |

### 3.2 Lineage Direction

Lineage must be documented in both directions:

- **Downstream (Provenance):** Consumer → Gold → Silver → Bronze → Raw → Source
- **Upstream (Impact):** Source → Raw → Bronze → Silver → Gold → Consumer

### 3.3 Lineage Data Model

Lineage is captured in the operational metadata system (PostgreSQL) and queryable through metadata APIs.

#### Lineage Record Structure

| Field | Description |
|---|---|
| `lineage_id` | Unique lineage record identifier |
| `source_dataset_id` | Upstream source dataset |
| `source_field` | Source field name (NULL for dataset-level) |
| `target_dataset_id` | Downstream target dataset |
| `target_field` | Target field name (NULL for dataset-level) |
| `transformation` | Description of the transformation applied |
| `transformation_code_ref` | Repository path to transformation logic |
| `transformation_version` | Version of transformation code |
| `pipeline_run_id` | Pipeline run that produced this lineage |
| `processing_timestamp` | When transformation occurred |
| `quality_status` | Quality outcome at this transformation step |

---

## 4. Lineage by Layer

### 4.1 Source → Raw

| Lineage Element | Description |
|---|---|
| Source | External institution and dataset |
| Raw Object | Exact payload stored with acquisition metadata |
| Transformation | Fetch, validate, and persist |
| Traceability | Content hash, retrieval timestamp, source version |

### 4.2 Raw → Bronze

| Lineage Element | Description |
|---|---|
| Source | Raw payload |
| Bronze Record | Parsed, source-aligned, minimally normalized |
| Transformation | Parse, normalize types, attach ingestion metadata |
| Traceability | Source field mapping preserved; raw field → bronze field mapping documented |

### 4.3 Bronze → Silver

| Lineage Element | Description |
|---|---|
| Source | Bronze dataset |
| Silver Record | Standardized enterprise data structure |
| Transformation | Canonical field mapping, type standardization, deduplication, validation |
| Traceability | Bronze field → Silver field mapping documented; canonical field name documented |

### 4.4 Silver → Gold

| Lineage Element | Description |
|---|---|
| Source | Silver dataset |
| Gold Record | Consumer-oriented data product |
| Transformation | Business aggregation, derivation, enrichment |
| Traceability | Silver metric → Gold metric mapping documented; calculation formula documented |

---

## 5. Lineage Documentation Standards

### 5.1 Metadata Documentation

Every dataset and transformation must document:

- Source dataset and fields
- Target dataset and fields
- Transformation logic description
- Code repository reference
- Transformation version
- Any field-level mappings or derivations

### 5.2 Data Contract Lineage Section

Each Data Contract includes a `lineage` section specifying:

- Upstream source dependencies
- Transformation steps from source to product
- Downstream consumers
- Lineage coverage level (dataset or field)

### 5.3 Data Dictionary Lineage

The Data Dictionary documents canonical field definitions and their source mappings. Each canonical metric references its source-origin metric names and transformation rules.

---

## 6. Lineage Verification

### 6.1 Verification Cadence

| Activity | Frequency | Owner |
|---|---|---|
| Lineage completeness check | Monthly | Data Owner |
| Lineage accuracy audit | Quarterly | Data Governance |
| Lineage integrity test (on source change) | Per source change | Technical Owner |
| Production readiness lineage verification | Per dataset | Data Governance |

### 6.2 Lineage Integrity Checks

- All Gold products have documented lineage to source
- All transformations have code references
- Field-level mappings are complete and accurate
- Lineage is not broken by schema changes
- Version tracking is current

### 6.3 Broken Lineage Handling

When lineage is broken (e.g., source schema change, transformation rewrite):

1. Flag broken lineage immediately
2. Assess impact on downstream consumers
3. Update lineage documentation
4. Verify lineage integrity before next publication
5. Document the break and repair in the change log

---

## 7. Lineage Tools and Storage

- Lineage metadata stored in PostgreSQL (operational metadata)
- Lineage queryable through metadata APIs
- Lineage visualized through lineage graph tools
- Lineage history preserved alongside dataset versioning

---

## 8. Lineage and Reproducibility

Lineage directly supports reproducibility:

- Each observation records `source_version`, `transformation version`, and `pipeline_run_id`
- Historical reconstruction uses lineage to identify exact inputs and transformations
- Point-in-time analysis uses effective_from/effective_to tracking

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — lineage standards, verification, documentation, and integration with reproducibility |

---

## 10. Document Status

This Lineage Policy is a draft artifact subject to stakeholder review and approval. It is a companion to the Data Governance Policy, Data Dictionary, Data Contracts, and PRD Section 9 (Lineage requirements).

---

*This document is classified as Internal. Distribution is restricted to authorized FINDEX team members and stakeholders.*