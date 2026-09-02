# ADR-007 — Temporal and Versioning Model

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

Financial and economic data involves multiple temporal concepts that are often confused:

- **Observation time**: When the economic event/measurement refers to
- **Publication time**: When the source published the information
- **Ingestion time**: When FINDEX acquired it

Additionally, source institutions may revise historical data. The platform must handle these temporal semantics correctly and support historical reconstruction without overwriting prior observations.

The system must not assume that `observation_date = publication_date = ingestion_date` when the source provides different semantics.

---

## Decision

FINDEX shall implement a temporal model that explicitly distinguishes observation time, publication time, and ingestion time, and a versioning model that preserves historical observations using effective_from/effective_to tracking rather than overwriting.

---

## Alternatives Considered

### Alternative A: Single Timestamp

Use a single timestamp for all temporal concepts.

| Aspect | Assessment |
|---|---|
| Pros | Simple; easy to implement |
| Cons | Loses critical temporal semantics; cannot distinguish observation from publication; violates PRD Section 14 |
| Verdict | **Rejected** |

### B: Explicit Temporal Model (Selected)

Separate fields for observation_date, publication_date, ingestion_timestamp, effective_from, effective_to.

| Aspect | Assessment |
|---|---|
| Pros | Preserves all temporal semantics; supports historical reconstruction; aligns with PRD and Data Dictionary |
| Cons | More complex schema; requires careful handling |
| Verdict | **Selected** |

### Alternative C: Event Sourcing

All changes stored as immutable events.

| Aspect | Assessment |
|---|---|
| Pros | Full history preserved; complete audit trail |
| Cons | Over-engineering for initial release; significant operational complexity |
| Verdict | **Rejected** |

---

## Consequences

### Positive

1. **Temporal clarity** — All stakeholders understand what each timestamp means
2. **Historical reconstruction** — Point-in-time analysis is supported
3. **Revision tracking** — Historical revisions are preserved, not overwritten
4. **Reproducibility** — Processing results reproducible using recorded temporal metadata
5. **Consumer confidence** — Temporal semantics are explicit and documented

### Negative

1. **Schema complexity** — Additional temporal fields increase schema complexity
2. **Query complexity** — Temporal queries require understanding of multiple time concepts
3. **Storage overhead** — Preserving historical versions increases storage (mitigated by raw data immutability)

---

## Temporal Model

```text
Observation Time → When the economic event/measurement refers to
Publication Time → When the source published the information
Ingestion Time   → When FINDEX acquired it
Effective From   → When this observation became authoritative
Effective To     → When this observation was superseded (NULL = current)
```

---

## Versioning Model

- **effective_from** set to ingestion timestamp when observation first becomes authoritative
- **effective_to** set to revision timestamp when observation is superseded
- **is_revised** flag indicates whether observation replaces a prior version
- **prior_observation_id** references the superseded observation
- Prior observations are never deleted — always preserved with effective_to set
- Gold layer data products reflect latest revision unless point-in-time analysis requested

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage — raw data with timestamps |
| ADR-003 | Canonical model — temporal fields in observation model |
| ADR-008 | Storage tiering — temporal data affects retention |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*