# ADR-002 — Source Ingestion Interface

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX must ingest data from heterogeneous external sources — OJK, BI, BPS, and other official institutions. These sources differ in:

- Access mechanisms (API, file download, web portal)
- Authentication methods (API key, OAuth, institutional access)
- Data formats (JSON, Excel, CSV, PDF)
- Publication schedules
- Rate limits and availability

A standardized ingestion interface is required to ensure consistent, reliable, and maintainable data acquisition across all sources while accommodating source-specific differences.

---

## Decision

Each source connector shall implement a common interface conceptually defined by the following methods:

```text
discover()
authenticate()
extract()
validate_response()
persist_raw()
emit_metadata()
```

The connector shall not contain downstream business logic. All business rules, transformations, and quality checks reside in the pipeline layers (Bronze, Silver, Gold), not in the connector.

---

## Alternatives Considered

### Alternative A: Monolithic Ingestion Service

A single monolithic service handles all sources with conditional logic per source.

| Aspect | Assessment |
|---|---|
| Pros | Centralized; simpler initial implementation |
| Cons | Tight coupling; difficult to maintain; single point of failure; hard to test per source |
| Verdict | **Rejected** — Violates modularity and maintainability principles |

### Alternative B: Standardized Connector Interface (Selected)

Each source implements a common interface.

| Aspect | Assessment |
|---|---|
| Pros | Modular; testable per source; maintainable; extensible; each connector is independently deployable |
| Cons | Interface definition requires upfront investment; connector implementations may vary |
| Verdict | **Selected** — Best alignment with FINDEX principles |

### Alternative C: Message Queue-Based Ingestion

All sources push data to a message queue for downstream processing.

| Aspect | Assessment |
|---|---|
| Pros | Decoupled; scalable |
| Cons | Over-engineering for initial use case; adds operational complexity; not needed for scheduled batch ingestion |
| Verdict | **Rejected** — Premature complexity |

---

## Consequences

### Positive

1. **Consistency** — All connectors follow the same interface contract
2. **Testability** — Each connector can be tested independently
3. **Maintainability** — Source-specific logic is isolated in each connector
4. **Extensibility** — New sources are onboarded by implementing the interface
5. **Separation of Concerns** — Connectors handle acquisition only; business logic is in pipeline layers
6. **Reusability** — Common infrastructure (retry, logging, metadata) is shared across connectors

### Negative

1. **Interface overhead** — Common interface adds abstraction layer
2. **Connector variability** — Some sources require significant adapter work
3. **Upfront design effort** — Interface must be defined before implementation

---

## Source Priority

Preferred ingestion order per TDD Section 13.2:

1. **Official API** — Preferred mechanism for structured, programmatic access
2. **Official downloadable dataset** — Preferred for batch data distribution
3. **Official portal** — For web-based data access
4. **Official web extraction** — Controlled fallback when necessary

Scraping is a controlled fallback, not the default ingestion method.

---

## Interface Method Definitions

### discover()
Returns available datasets, metadata, and access information for the source.

### authenticate()
Establishes authenticated session using source-appropriate method (API key, OAuth, institutional credentials).

### extract()
Retrieves data from the source using the established connection. Returns raw payload.

### validate_response()
Validates the response structure, integrity, and completeness before processing.

### persist_raw()
Stores the raw payload in object storage with full acquisition metadata.

### emit_metadata()
Records ingestion metadata including run_id, source_id, dataset_id, timestamps, record counts, and quality indicators.

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage as raw data sink |
| ADR-003 | Canonical data model — connector outputs map to canonical model |
| ADR-004 | Orchestration — Airflow invokes connectors |
| ADR-007 | Temporal/versioning — connector captures source_version |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*