# ADR-001 — Object Storage as Primary Historical Storage Layer

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX requires durable, scalable, and cost-effective storage for:

1. **Raw source payloads** — Immutable archives of all ingested data
2. **Bronze/Silver/Gold layers** — Transformed data at various stages of refinement
3. **Quarantine data** — Failed records requiring investigation
4. **Operational metadata** — Pipeline execution logs and audit trails

The platform must support:

- Petabyte-scale growth as datasets increase
- Long-term retention (10+ years) for historical analysis
- Cost-efficient storage of cold/historical data
- Separation of storage from compute for flexible processing
- Multiple downstream consumers (Athena, Spark, dbt, BI tools)
- Local development parity (MinIO-compatible)
- Reproducible infrastructure via IaC

---

## Decision

Object storage (S3-compatible, with MinIO for local development) shall be the primary storage layer for all historical and analytical data in the FINDEX platform. Relational databases (PostgreSQL) shall be reserved exclusively for operational metadata, control tables, and the data catalog — not for analytical data storage.

---

## Alternatives Considered

### Alternative A: Relational Database (PostgreSQL) for All Data

| Aspect | Assessment |
|---|---|
| Pros | Strong ACID guarantees; familiar technology; mature ecosystem |
| Cons | Poor scalability for large historical datasets; high storage cost; vertical scaling limitations; expensive backup/restore at scale |
| Verdict | **Rejected** — Cannot support petabyte-scale historical data cost-effectively |

### Alternative B: Data Warehouse (Snowflake / BigQuery)

| Aspect | Assessment |
|---|---|
| Pros | Managed service; excellent query performance; built-in caching |
| Cons | Vendor lock-in; unpredictable costs at scale; limited control over storage layout; less suitable for immutable raw data preservation |
| Verdict | **Rejected** — Over-engineering for initial use case; cost model misaligned with immutable raw storage requirements |

### Alternative C: Object Storage + Compute Separation (Selected)

| Aspect | Assessment |
|---|---|
| Pros | Extremely cost-effective at scale; virtually unlimited scalability; immutable storage support; compute-storage separation; multi-format support (Parquet, JSON, CSV); lifecycle policies for cost management; MinIO-compatible for local development |
| Cons | Requires explicit partition strategy; query performance depends on file format and partitioning; no built-in ACID transactions (mitigated by dbt and Delta Lake if needed) |
| Verdict | **Selected** — Best alignment with FINDEX requirements |

### Alternative D: Data Lakehouse with Delta Lake / Apache Iceberg

| Aspect | Assessment |
|---|---|
| Pros | ACID transactions; time travel; schema enforcement; built on object storage |
| Cons | Added complexity; may be premature for initial release; can be adopted incrementally if needed |
| Verdict | **Defer** — Object storage foundation established now; lakehouse layer added later if transaction requirements demand it |

---

## Consequences

### Positive

1. **Cost Efficiency**: Object storage is orders of magnitude cheaper than relational or warehouse storage for large historical datasets
2. **Scalability**: Virtually unlimited scalability without architectural redesign
3. **Local Development Parity**: MinIO provides an S3-compatible local storage layer, enabling full platform reproduction in development environments
4. **Separation of Concerns**: Storage is independent of compute; Athena, Spark, dbt, and other engines can access the same data
5. **Immutable Preservation**: Object storage naturally supports immutable raw data storage
6. **Lifecycle Management**: Automatic tiering (frequent access → infrequent access → archive) controls costs
7. **Format Flexibility**: Parquet, JSON, CSV, and future formats can coexist

### Negative

1. **No Built-in ACID**: Concurrent writes require additional tooling (Delta Lake, Iceberg) — deferred to future if needed
2. **Partitioning Responsibility**: Engineers must design partition strategies explicitly — mitigated by documented conventions in TDD Section 37
3. **Query Performance**: Depends on file format, partitioning, and compute engine configuration — mitigated by Parquet + partition pruning + predicate pushdown
4. **Operational Complexity**: Managing object storage lifecycle policies, encryption, and access controls adds operational overhead — mitigated by IaC (Terraform)

### Neutral

1. **Technology Choice**: S3 for production, MinIO for local development — this is a pragmatic split, not an architectural inconsistency
2. **Format Selection**: Parquet for analytical data, JSON for raw payloads — documented in TDD Section 38

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-002 (TBD) | Source ingestion interface design — depends on object storage as raw data sink |
| ADR-003 (TBD) | Canonical data model strategy — defines data structure stored in object storage |
| ADR-004 (TBD) | Orchestration technology — Airflow produces pipeline artifacts stored in object storage |
| ADR-005 (TBD) | Transformation framework — dbt/Spark write outputs to object storage |
| ADR-006 (TBD) | Cloud deployment strategy — S3 is the AWS object storage service |
| ADR-007 (TBD) | Temporal/versioning model — version tracking stored in object storage metadata |

---

## Implementation Notes

### Storage Layout

```text
s3://findex-data/
├── raw/
│   ├── source=ojk/
│   │   └── dataset=banking_stats/
│   │       └── ingestion_date=2026-09-01/
│   │           └── run_id=<run_id>/
│   │               ├── payload.parquet (or .json/.csv)
│   │               └── manifest.json
├── bronze/
│   └── ... (same partition structure)
├── silver/
│   └── ...
├── gold/
│   └── ...
├── quarantine/
│   └── ...
└── metadata/
    └── ...
```

### Partition Strategy

| Layer | Partition Dimensions | Rationale |
|---|---|---|
| Raw | `source`, `dataset`, `ingestion_date` | Traceability and reprocessing |
| Bronze | `source`, `dataset`, `ingestion_date` | Source-level reconstruction |
| Silver | `source`, `dataset`, `observation_year`, `observation_month` | Time-series analytical access |
| Gold | `product`, `observation_year`, `observation_month` | Consumer-oriented access |

### Lifecycle Policies

| Tier | Storage Class | Transition | Retention |
|---|---|---|---|
| Hot | Standard | Immediate | 0–90 days |
| Warm | Infrequent Access | After 90 days | 90 days–2 years |
| Cold | Glacier / Archive | After 2 years | 2–10 years |
| Archive | Deep Archive | After 10 years | Per retention policy |

### Security

- Server-side encryption (SSE-S3 or SSE-KMS)
- Bucket policies enforcing least-privilege access
- Access logging enabled
- No public access buckets
- Versioning enabled on raw and quarantine buckets

---

## Open Questions

1. Should Delta Lake or Apache Iceberg be adopted for ACID transactions on Silver/Gold layers? (Deferred — object storage foundation is sufficient for Release 1)
2. What is the optimal Parquet file size target? (Recommendation: 128MB–1GB; validated after profiling)
3. Should cross-region replication be implemented for disaster recovery? (Deferred until RPO/RTO are defined)

---

## References

- **PRD** Section 16 — Non-Functional Requirements (Scalability, Reliability)
- **PRD** Section 17 — Non-Functional Requirements (Performance)
- **TDD** Section 6 — Data Lakehouse Layout
- **TDD** Section 36 — AWS Architecture
- **TDD** Section 37 — Storage Strategy
- **TDD** Section 38 — File Formats

---

*This ADR is classified as Internal. Distribution is restricted to authorized FINDEX team members.*