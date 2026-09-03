# ADR-001 — Object Storage as Primary Historical Storage Layer

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §11, §34 (cost governance); TDD §6, §7, §36, §37, §38  

---

## Context

KLIBRA requires durable, scalable, and cost-effective storage for:

1. **Raw source payloads** — Immutable archives of all ingested data.
2. **Bronze / Silver / Gold layers** — Transformed data at each stage of refinement.
3. **Quarantine data** — Failed records requiring investigation.
4. **Operational metadata** — Pipeline execution logs and audit trails.

The platform must support:

- Petabyte-scale growth as datasets increase.
- Long-term retention (10+ years) for historical reconstruction (PRD §4.2).
- Cost-efficient storage of cold/historical data (PRD §34).
- Separation of storage from compute for flexible processing.
- Multiple downstream consumers (Athena / Trino, Spark, dbt, BI tools).
- Local development parity (MinIO-compatible).
- Reproducible infrastructure via IaC (TDD §34).
- Revision-aware preservation where source history exists (TDD §70).

---

## Decision

Object storage (S3-compatible, with MinIO for local development) shall be the **primary storage layer** for all historical and analytical data in the KLIBRA platform.

Relational databases (PostgreSQL) shall be reserved exclusively for the **operational control plane** — pipeline metadata, run state, dataset registry, configuration. They shall **not** be used as the primary storage for analytical data (TDD §39).

---

## Alternatives Considered

- **Alternative A: Relational Database (PostgreSQL) for All Data** — Rejected. Cannot support petabyte-scale historical data cost-effectively; no native immutable-raw semantics.
- **Alternative B: Data Warehouse (Snowflake / BigQuery)** — Rejected. Cost model misaligned with immutable raw storage and frequent revision preservation.
- **Alternative C: Object Storage + Compute Separation (Selected)** — Best alignment with KLIBRA's requirements: durability, scalability, local parity, format independence, IaC compatibility.
- **Alternative D: Data Lakehouse with Delta Lake / Apache Iceberg** — Defer. Object storage foundation established now; lakehouse table format added when measured workload justifies transaction/time-travel semantics (TDD §4, §37).

---

## Consequences

**Positive:**

- Cost efficiency via lifecycle policies (PRD §34).
- Scalability decoupled from compute.
- Local development parity through MinIO (TDD §35).
- Separation of concerns between storage and processing.
- Immutable preservation of raw payloads (TDD §2.1, §7).
- Lifecycle management aligned with retention policy (PRD §50 / TDD §50).
- Format flexibility (Parquet / JSON / CSV per TDD §38).

**Negative:**

- No built-in ACID — mitigated via deterministic, idempotent transformations and Iceberg when justified.
- Partitioning responsibility falls on engineering — controlled by storage strategy (TDD §37).
- Query performance depends on file format and partitioning — controlled by §37, §38.
- Operational complexity — mitigated by Terraform IaC and operational runbooks.

---

## Storage Layout

```text
s3://klibra-data/
├── raw/
│   ├── source=<source_id>/
│   │   └── dataset=<dataset_id>/
│   │       └── ingestion_date=<YYYY-MM-DD>/
│   │           └── run_id=<run_id>/
│   │               ├── payload
│   │               └── manifest.json
├── bronze/
├── silver/
├── gold/
├── quarantine/
└── metadata/
```

Logical layering aligns with TDD §6:

| Layer | Purpose |
| --- | --- |
| `raw/` | Exact source payloads and acquisition metadata |
| `bronze/` | Source-aligned, minimally normalized |
| `silver/` | Standardized, validated analytical entities |
| `gold/` | Consumer-oriented data products |
| `quarantine/` | Records or batches failing blocking controls |
| `metadata/` | Operational metadata (run state, manifests) |

---

## Partition Strategy

| Layer | Partition Dimensions |
| --- | --- |
| Raw | `source`, `dataset`, `ingestion_date` |
| Bronze | `source`, `dataset`, `ingestion_date` |
| Silver | `source`, `dataset`, `observation_year`, `observation_month` |
| Gold | `product`, `observation_year`, `observation_month` |

Partitioning must not over-fragment small datasets (TDD §37). The final strategy is tuned after measured workload.

---

## Lifecycle Policies

| Tier | Storage Class | Transition | Retention |
| --- | --- | --- | --- |
| Hot | Standard | Immediate | 0–90 days |
| Warm | Infrequent Access | After 90 days | 90 days–2 years |
| Cold | Glacier / Archive | After 2 years | 2–10 years |
| Archive | Deep Archive | After 10 years | Per retention policy |

---

## Security

- SSE-S3 or SSE-KMS encryption at rest.
- Bucket policies enforcing least-privilege access (PRD §16, §33; TDD §31).
- Access logging enabled.
- No public access.
- Versioning on raw and quarantine buckets (revision preservation — TDD §70).
- Encryption in transit enforced at client side.

---

## Definition of Done

This ADR is implemented when:

- Object storage is the primary storage layer in production, staging, and local environments.
- Local environment uses MinIO with the same layout.
- Raw layer enforces immutability and versioning.
- Lifecycle policies are active and observable.
- Partition strategy is in place and documented per layer.
- Security controls are verified (encryption, access logs, no public access).
