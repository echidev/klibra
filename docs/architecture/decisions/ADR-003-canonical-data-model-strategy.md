# ADR-003 — Canonical Data Model Strategy

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX ingests data from multiple authoritative sources (OJK, BI, BPS) that use different structures, terminology, classifications, and granularities. Without a unifying model, downstream consumers would need to understand and reconcile these differences, defeating the purpose of a governed data platform.

The platform must provide a single, standardized view of financial data while preserving source-specific detail in the Bronze layer.

---

## Decision

FINDEX shall adopt an observation-centric canonical data model as the unifying structure for all financial and macroeconomic data. The model defines a core fact table (`fact_financial_observation`) and supporting dimensions (`dim_metric`, `dim_entity`, `dim_geography`, `dim_sector`, `dim_source`, `dim_dataset`, `dim_calendar`).

Where source data is compatible, it is mapped to this canonical model. Source-specific structures are preserved in the Raw and Bronze layers. The canonical model is defined in the Data Dictionary and is subject to refinement as source data is profiled.

---

## Alternatives Considered

### Alternative A: Source-Aligned Models

Each downstream layer preserves source-specific structures.

| Aspect | Assessment |
|---|---|
| Pros | No mapping needed; preserves source fidelity |
| Cons | Consumers must understand every source structure; no standardization; defeats platform purpose |
| Verdict | **Rejected** — Contradicts platform objective of standardization |

### B: Canonical Observation Model (Selected)

A single observation-centric model unifies all sources.

| Aspect | Assessment |
|---|---|
| Pros | Standardized consumer interface; semantic consistency; supports cross-source analysis; traceability preserved |
| Cons | Mapping effort for each source; some metrics may not map cleanly |
| Verdict | **Selected** — Aligns with platform vision and Data Dictionary |

### Alternative C: Star Schema Only

Traditional star schema with fact and dimension tables.

| Aspect | Assessment |
|---|---|
| Pros | Well-understood; good query performance |
| Cons | Less flexible for financial time-series data; observation-centric model better supports temporal semantics |
| Verdict | **Rejected** — Observation model better serves FINDEX temporal requirements |

---

## Consequences

### Positive

1. **Standardization** — All data consumers use the same canonical structure
2. **Cross-source analysis** — Compatible sources can be compared and combined
3. **Traceability** — Source-to-canonical mappings are documented
4. **Flexibility** — Source-specific detail preserved in Bronze layer
5. **Consumer simplicity** — Downstream users interact with canonical model, not source structures
6. **Extensibility** — New sources map to canonical model without restructuring downstream consumers

### Negative

1. **Mapping effort** — Each source requires field mapping and transformation logic
2. **Incompatible sources** — Some source data may not map cleanly; handled via Bronze layer
3. **Model evolution** — Canonical model may need to expand as new sources are onboarded

---

## Model Governance

- Canonical model defined in `docs/data/data_dictionary.md`
- Model changes follow change management process
- New metrics added to `dim_metric` with full definition
- Mapping from source fields to canonical fields documented in Data Dictionary
- Model version controlled alongside Data Dictionary

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage — canonical model data stored in object storage |
| ADR-002 | Source ingestion interface — connector output maps to canonical model |
| ADR-005 | Transformation framework — dbt transforms Bronze to Silver using canonical model |
| Data Dictionary | Defines the canonical model in detail |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*