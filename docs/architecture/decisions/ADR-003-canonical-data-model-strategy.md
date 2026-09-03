# ADR-003 — Canonical Data Model Strategy

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §11 (data products); TDD §11 (canonical model)  

---

## Context

KLIBRA ingests heterogeneous data from multiple public sources, each with its own schema, identifiers, units, and temporal conventions (PRD §10.1‑§10.5). A unified, observation‑centric model enables cross‑source analysis, reproducibility, and lineage (TDD §11‑§12).

---

## Decision

Adopt a **canonical observation model** (`fact_economic_observation`) with supporting dimension tables. The model is defined as:

```text
fact_economic_observation
--------------------------
observation_id            UUID primary key
metric_id                 FK → dim_metric.metric_id
entity_id                 FK → dim_entity.entity_id
geography_id              FK → dim_geography.geography_id
sector_id                 FK → dim_sector.sector_id
observation_date          DATE (Observation Time)
value                     DECIMAL
unit                      STRING
source_id                 FK → dim_source.source_id
dataset_id                FK → dim_dataset.dataset_id
publication_date          DATE (Publication Time)
ingestion_timestamp       TIMESTAMP (Ingestion Time)
effective_from            TIMESTAMP (effective start)
effective_to              TIMESTAMP (effective end, NULL=active)
source_version            STRING (source revision identifier)
quality_status            ENUM('ACCEPTED','ACCEPTED_WARNING','QUARANTINED','REJECTED')
```

Supporting dimensions (`dim_metric`, `dim_entity`, `dim_geography`, `dim_sector`, `dim_source`, `dim_dataset`, `dim_calendar`) capture static metadata, grain, and lineage (PRD §27, TDD §11‑§12).

---

## Alternatives Considered

- **Source‑Aligned Models** — Rejected. Hinders cross‑source reconciliation and metric consistency.
- **Canonical Observation Model (Selected)** — Aligns with PRD’s goal of unified economic intelligence and satisfies TDD’s temporal and versioning requirements.
- **Star‑Schema Only** — Rejected. Does not capture the full temporal semantics needed for revision handling (TDD §70).

---

## Implementation Details

- The model is defined in `docs/data/data_dictionary.md` and version‑controlled.
- New metrics added to `dim_metric` with full definition (name, description, grain, unit, formula) per PRD §27 and TDD §63.
- Source‑specific fields are retained in `raw/` and `bronze/` layers for auditability.
- Transformation logic from Bronze to Silver maps source fields onto the canonical model, applying unit conversion, entity mapping, and temporal alignment (TDD §7‑§12).
- Effective‑from/effective‑to fields enable **point‑in‑time reconstruction** (TDD §70) and support **historical backfills** (Runbook‑Backfill).

---

## Consequences

**Positive:**

- Enables cross‑source metric reconciliation (PRD §23, TDD §23).
- Provides deterministic, reproducible lineage.
- Supports revision‑aware historical queries and backfills.
- Simplifies downstream consumption: Gold products expose a stable, well‑documented schema.

**Negative:**

- Requires upfront effort to map all source schemas.
- May increase processing complexity in Silver layer.
- Changing the model later incurs migration effort; mitigated by ADR‑007 (temporal/versioning) and ADR‑008 (storage tiering).

---

## Definition of Done

- `fact_economic_observation` and all dimension tables are created in the `silver/` layer using dbt models.
- Unit tests cover field mapping, unit conversion, and temporal alignment.
- Data contracts for the canonical model are stored under `docs/data/contracts/gold/` and enforced by CI.
- Documentation updated in `docs/data/data_dictionary.md`.
- Review sign‑off from Data Governance and Technical Owner.
