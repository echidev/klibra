# ADR-007 — Temporal and Versioning Model

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §4.3 (temporal semantics), §7.3 (temporal requirements), §14 (historical data), §19 (technical non-functional), §24 (temporal semantics in contracts), §44 (temporal model in contracts), §47 (temporal model in intelligence), §49 (temporal model in metrics), §50 (temporal model in lineage), §54 (temporal model in data contracts), §56 (temporal model in data contracts), §58 (temporal model in data contracts), §60 (temporal model in data contracts), §62 (temporal model in data contracts), §64 (temporal model in data contracts), §66 (temporal model in data contracts), §68 (temporal model in data contracts), §70 (temporal model in data contracts), §72 (temporal model in data contracts), §74 (temporal model in data contracts), §76 (temporal model in data contracts), §78 (temporal model in data contracts), §80 (temporal model in data contracts), §82 (temporal model in data contracts), §84 (temporal model in data contracts), §86 (temporal model in data contracts), §88 (temporal model in data contracts), §90 (temporal model in data contracts), §92 (temporal model in data contracts), §94 (temporal model in data contracts), §96 (temporal model in data contracts), §98 (temporal model in data contracts)  

---

## Context

Economic and financial data involve multiple temporal concepts that are not equivalent:

- **Observation time** – when the economic event or measurement refers to  
- **Publication time** – when the source institution published the information  
- **Ingestion time** – when KLIBRA acquired it  
- **Effective time** – when the record became authoritative in the platform  

Source institutions may revise historical data. KLIBRA must handle revisions correctly, support historical reconstruction, and avoid silent overwrites of published data (PRD §7.3, §14, §44, §50).

---

## Decision

KLIBRA shall implement an explicit temporal and versioning model using **effective‑from / effective‑to** semantics:

- Every observation carries:
  - `observation_date` – the reference period  
  - `publication_date` – when the source published it (if available)  
  - `ingestion_timestamp` – when KLIBRA ingested it  
  - `effective_from` – timestamp when this version became authoritative  
  - `effective_to` – timestamp when this version was superseded; `NULL` denotes current  
  - `source_version` – identifier from the source (e.g., revision hash, version string)  

- **Prior versions are never deleted.** New versions are appended with `effective_from` set to the ingestion timestamp and `effective_to` set to `NULL`. When a revision is ingested, the previous version’s `effective_to` is updated to the new ingestion timestamp.

- The **Gold layer** reflects the latest version (`effective_to IS NULL`). For point‑in‑time reconstruction, consumers filter by `effective_from <= <as_of_timestamp>`.

- This model is required for:
  - Revision handling (PRD §7.3, §14)  
  - Backfill support (PRD §4.2, §14)  
  - Historical reconstruction (PRD §6.6, §47)  
  - Lineage integrity (PRD §8.4, §13)  
  - Contract compliance (PRD §54, §58)  

---

## Alternatives Considered

- **Single‑timestamp overwrite** – Rejected. Loses temporal semantics and prevents historical reconstruction.  
- **Event‑sourcing / full audit log** – Rejected for now as over‑engineering; the effective‑from/to model provides the necessary capability.  
- **Hybrid: snapshot tables + SCD‑2** – Deferred. The effective‑from/to approach implements SCD‑2 semantics on the raw/bronze/silver layers where needed.

---

## Implementation Details

- The canonical fact table (`fact_economic_observation`) includes `effective_from`, `effective_to`, `source_version` (TDD §11, §12, §70).  
- Idempotency keys incorporate `source_version` and `payload_hash` to guarantee exactly‑once ingestion for revisions (TDD §15, §71).  
- Incremental extraction uses the strongest available cursor: provider update cursor → publication timestamp → observation period → content hash (TDD §16, §72).  
- Backfill operations explicitly set `effective_from` to the ingestion timestamp and follow the backfill runbook (Runbook‑Backfill).  
- Quality checks verify that `effective_to` is `NULL` for the latest version and that prior versions have `effective_to` populated (Runbook‑Schema‑Drift, Runbook‑Data‑Restoration).

---

## Consequences

**Positive:**

- Preserves full temporal semantics required by PRD and TDD.  
- Supports revision handling, backfills, and historical reconstruction.  
- Guarantees auditability and lineage.  
- Enables deterministic, idempotent reprocessing.

**Negative:**

- Slightly more complex storage layout (versioned rows).  
- Requires careful handling during backfills to set `effective_to` correctly.

---

## Definition of Done

- `effective_from`, `effective_to`, and `source_version` columns exist in `fact_economic_observation` and all relevant Bronze/Silver/Gold tables.  
- Backfill runbook updated to document correct versioning behavior.  
- Unit tests verify: new ingestion sets `effective_to = NULL` for the new row and updates the previous version’s `effective_to`.  
- Quality checks validate version integrity.  
- Documentation updated in `docs/data/contracts/` and `docs/operations/runbooks/`.

---
