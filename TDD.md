# FINDEX — Technical Design Document

**Document Type:** Technical Design Document (TDD)  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Architecture Baseline / Subject to Source Validation  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Platform Engineering  
**Classification:** Internal

---

# 1. Purpose

This document defines the technical architecture, engineering standards, operational model, and implementation approach for FINDEX.

The TDD translates the approved product requirements into an implementable engineering design.

The architecture is intentionally designed to support:

- Heterogeneous external sources
- Historical preservation
- Data quality enforcement
- Reproducible processing
- Incremental processing
- Backfills
- Schema evolution
- Metadata and lineage
- Operational observability
- Controlled access
- Local development
- Production cloud deployment

Technology choices in this document are recommendations subject to source-level feasibility validation.

---

# 2. Design Principles

## 2.1 Raw Data Is Immutable

Source payloads should be preserved in their received form.

## 2.2 Transformations Are Deterministic

Transformations should be reproducible from versioned code, configuration, and source inputs.

## 2.3 Every Dataset Has an Owner

Ownership is required for operational accountability.

## 2.4 Quality Gates Are Explicit

Data must not silently progress through the platform when blocking checks fail.

## 2.5 Operational Metadata Is First-Class Data

Pipeline execution information must be stored and queryable.

## 2.6 Idempotency by Default

Repeating a pipeline run must not unintentionally duplicate published data.

## 2.7 Separate Storage From Serving

Storage layers preserve and process data; serving layers optimize access patterns.

## 2.8 Prefer Boring Technology

Stable, well-understood technology is preferred over unnecessary architectural novelty.

---

# 3. Logical Architecture

```text
                    External Sources
          ┌────────────┬────────────┬────────────┐
          │            │            │            │
         OJK           BI          BPS      Other Official
          │            │            │            │
          └────────────┴────────────┴────────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Source Connectors  │
                 │ API / File / Web   │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Raw / Landing     │
                 │ Immutable         │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Bronze            │
                 │ Source-aligned    │
                 └─────────┬─────────┘
                           │
                    Quality Gates
                           │
                           ▼
                 ┌───────────────────┐
                 │ Silver            │
                 │ Standardized      │
                 └─────────┬─────────┘
                           │
                    Business Rules
                           │
                           ▼
                 ┌───────────────────┐
                 │ Gold              │
                 │ Data Products     │
                 └─────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
         Analytics       API/BI       Data Science
```

---

# 4. Technology Strategy

The platform will use technology according to workload characteristics.

## Candidate Core Stack

| Capability | Candidate Technology | Purpose |
|---|---|---|
| Object Storage | S3 / MinIO | Durable data lake storage |
| Relational Metadata | PostgreSQL | Operational metadata and control plane |
| Orchestration | Apache Airflow | Scheduling and dependency management |
| Processing | Spark | Distributed transformation when required |
| SQL Transformation | dbt | Curated relational transformations |
| Local Analytics | DuckDB | Local analytical workloads |
| Containerization | Docker | Reproducible environments |
| CI/CD | GitHub Actions | Automated validation and deployment |
| IaC | Terraform | Reproducible infrastructure |
| Cloud Analytics | Athena | Serverless querying of lake data |
| Cloud Processing | AWS Glue | Managed ETL where economically justified |
| Monitoring | CloudWatch / OpenTelemetry | Platform observability |
| Secrets | AWS Secrets Manager | Production secret management |

The final stack shall be validated against actual source volume and operational requirements.

---

# 5. Environment Architecture

Three environments are recommended:

```text
Development
    ↓
Staging
    ↓
Production
```

## Development

Used for local engineering and experimentation.

## Staging

Used for integration testing and production-like validation.

## Production

Contains trusted published data products.

Production data must not be modified manually through ad-hoc engineering actions.

---

# 6. Data Lakehouse Layout

Recommended logical layers:

```text
/raw
/bronze
/silver
/gold
/quarantine
/metadata
```

## Raw

Exact source payloads and acquisition metadata.

## Bronze

Source-aligned, minimally normalized representations.

## Silver

Standardized and validated analytical entities.

## Gold

Consumer-oriented data products.

## Quarantine

Records or batches failing blocking controls.

---

# 7. Raw Data Design

Each ingestion should preserve:

- Source identifier
- Dataset identifier
- Retrieval timestamp
- Source publication timestamp if available
- Source URL/API identifier
- Request parameters where appropriate
- Response metadata
- Content hash
- File/payload format
- Pipeline run identifier
- Connector version

Suggested object convention:

```text
raw/
  source=<source_id>/
    dataset=<dataset_id>/
      ingestion_date=<YYYY-MM-DD>/
        run_id=<run_id>/
          payload
          manifest.json
```

Raw payloads should be immutable.

---

# 8. Bronze Layer

Bronze maintains source fidelity while making data queryable.

Responsibilities:

- Parse source payloads
- Preserve source fields
- Normalize technical types
- Attach ingestion metadata
- Record source version
- Detect malformed records

Bronze must not apply aggressive business interpretation.

---

# 9. Silver Layer

Silver provides standardized enterprise data structures.

Responsibilities:

- Canonical field names
- Standard data types
- Standard geographic identifiers
- Standard temporal representation
- Controlled classifications
- Deduplication
- Referential integrity
- Business validation
- Source reconciliation where required

Silver is the principal reusable engineering layer.

---

# 10. Gold Layer

Gold contains business-oriented data products.

Examples:

```text
gold_credit_growth
gold_financial_sector_monitor
gold_macro_financial_context
gold_regional_financial_profile
```

Gold models should optimize for consumer usability rather than source fidelity.

---

# 11. Canonical Data Model

The platform should use a canonical observation model where compatible sources permit.

Conceptual structure:

```text
fact_financial_observation
--------------------------------
observation_id
metric_id
entity_id
geography_id
sector_id
observation_date
value
unit
source_id
dataset_id
publication_date
ingestion_timestamp
effective_from
effective_to
source_version
quality_status
```

Supporting dimensions:

```text
dim_metric
dim_entity
dim_geography
dim_sector
dim_source
dim_calendar
```

The exact schema must be finalized after source profiling.

---

# 12. Temporal Data Model

The platform must distinguish multiple temporal concepts.

```text
Observation Time
      │
      ├── When the economic event/measurement refers to
      │
Publication Time
      │
      ├── When the source published the information
      │
Ingestion Time
      │
      └── When FINDEX acquired it
```

Where source revisions matter, version/effective-date handling should allow historical reconstruction.

A valid design must avoid overwriting historical observations without preserving the fact that a revision occurred.

---

# 13. Ingestion Architecture

## 13.1 Connector Pattern

Each source connector should implement a common interface conceptually equivalent to:

```text
discover()
authenticate()
extract()
validate_response()
persist_raw()
emit_metadata()
```

The connector should not contain downstream business logic.

## 13.2 Source Priority

Preferred order:

1. Official API
2. Official downloadable dataset
3. Official portal
4. Official web extraction when necessary

Scraping is a controlled fallback, not the default ingestion method.

---

# 14. Ingestion Metadata

Every pipeline execution should record:

```text
run_id
pipeline_id
dataset_id
source_id
started_at
completed_at
status
records_received
records_written
records_rejected
payload_hash
source_version
max_observation_date
min_observation_date
schema_version
error_type
error_message
```

This metadata forms part of the operational control plane.

---

# 15. Idempotency

Every ingestion pipeline must define an idempotency key.

Potential components:

```text
source_id
dataset_id
source_period
source_version
payload_hash
```

Reprocessing the same source payload must not create duplicate published observations.

---

# 16. Incremental Processing

Incremental ingestion should use the strongest available source signal:

1. Source cursor
2. Publication timestamp
3. Last modified timestamp
4. Source period
5. Content hash comparison

If no reliable incremental mechanism exists, the connector may perform bounded or full extraction followed by deterministic deduplication.

---

# 17. Backfill Strategy

Backfills must be explicit operations.

A backfill should specify:

- Dataset
- Start period
- End period
- Reason
- Requested by
- Code version
- Expected impact
- Validation status

Backfills must not silently overwrite production history.

---

# 18. Late-Arriving Data

Late-arriving records shall be accepted when valid.

The pipeline should distinguish:

- Observation date
- Arrival date
- Publication date

Downstream models must be able to account for delayed arrival.

---

# 19. Schema Evolution

Schema changes should be detected before promotion.

Change classes:

### Compatible

Examples:

- New nullable field
- Metadata-only change

### Potentially Breaking

Examples:

- Type widening/narrowing
- New required field
- Changed categorical values

### Breaking

Examples:

- Removed field
- Semantic redefinition
- Structural incompatibility

Breaking changes require review and controlled deployment.

---

# 20. Data Contracts

Each production dataset should have a contract covering:

```text
Dataset identity
Owner
Purpose
Schema
Field definitions
Data types
Units
Allowed values
Keys
Freshness expectation
Quality thresholds
Temporal semantics
Source
Versioning
Known limitations
```

Contracts should be version-controlled.

---

# 21. Data Quality Framework

Quality should operate at multiple levels.

## Batch-Level

- File exists
- Payload readable
- Expected response
- Record count
- Hash
- Schema

## Record-Level

- Type validity
- Nullability
- Range
- Allowed values
- Referential integrity

## Dataset-Level

- Duplicate rate
- Completeness
- Freshness
- Temporal continuity
- Cross-field consistency

## Business-Level

- Domain-specific business rules
- Reconciliation
- Expected relationships

---

# 22. Quality Severity

```text
P0 — Critical
Production data unsafe or platform integrity compromised.

P1 — High
Critical dataset cannot be trusted or is materially incomplete.

P2 — Medium
Quality degradation with usable but constrained output.

P3 — Low
Non-blocking anomaly or metadata/documentation issue.
```

Blocking P0/P1 conditions should prevent publication.

---

# 23. Quarantine Model

Failed data should be isolated.

Conceptual flow:

```text
Source
  ↓
Raw
  ↓
Validation
  ├── Pass → Bronze/Silver → Gold
  │
  └── Fail → Quarantine
                   ↓
              Investigation
                   ↓
             Correct / Replay
```

Quarantine records should retain:

- Run ID
- Dataset
- Failure rule
- Failed value/record reference
- Timestamp
- Error details

---

# 24. Transformation Architecture

Recommended separation:

### Python

Use for:

- API clients
- File extraction
- Source-specific parsing
- Complex procedural logic

### Spark

Use when:

- Data volume warrants distributed processing
- Large historical transformations require parallelism

### dbt

Use for:

- SQL-based transformations
- Data tests
- Documentation
- Dependency graphs

### DuckDB

Use for:

- Local analytical validation
- Lightweight development
- Ad-hoc inspection

---

# 25. Orchestration

Airflow is the candidate orchestration platform.

Conceptual DAG:

```text
discover
   ↓
extract
   ↓
raw_validation
   ↓
bronze
   ↓
quality_gate
   ↓
silver
   ↓
silver_quality
   ↓
gold
   ↓
publish
   ↓
notify
```

Tasks should be independently observable and retryable.

---

# 26. Pipeline Failure Handling

Failures should classify into:

- Authentication
- Network
- Source availability
- Rate limiting
- Schema change
- Parsing
- Data quality
- Transformation
- Storage
- Dependency
- Infrastructure

Retry behavior must depend on failure type.

For example:

- Network timeout → retry
- Authentication failure → alert, do not blindly retry
- Schema-breaking change → stop and investigate
- Data-quality anomaly → quarantine or block publication

---

# 27. Metadata Architecture

The metadata system should contain:

### Technical Metadata

- Dataset
- Schema
- Table
- Field
- Type
- Partition
- Location

### Operational Metadata

- Run
- Duration
- Status
- Records
- Errors
- Freshness

### Business Metadata

- Definition
- Owner
- Classification
- Usage
- Business glossary

---

# 28. Data Lineage

Lineage should represent:

```text
Source
  ↓
Raw Object
  ↓
Bronze Dataset
  ↓
Silver Model
  ↓
Gold Data Product
  ↓
Consumer
```

Lineage should be available at dataset level initially and field level where practical.

---

# 29. Observability

FINDEX requires two categories of observability.

## Platform Observability

- CPU
- Memory
- Disk
- Network
- Job duration
- Task failures

## Data Observability

- Freshness
- Row count
- Null rate
- Duplicate rate
- Distribution anomalies
- Schema changes
- Missing periods
- Quality failures

A pipeline can be technically healthy while producing bad data; both dimensions must therefore be monitored.

---

# 30. Alerting

Alerts should be:

- Actionable
- Deduplicated
- Severity-based
- Routed to responsible owners
- Linked to relevant run metadata

Alert examples:

```text
Dataset freshness breached
Schema breaking change detected
P1 quality rule failed
Source unavailable
Pipeline exceeded runtime threshold
Unexpected record-count change
```

---

# 31. Security Architecture

Security controls:

- IAM least privilege
- Environment isolation
- Secrets Manager
- No credentials in source code
- Encryption in transit
- Encryption at rest
- Role-based access
- Audit logs
- Controlled production access

Public data does not eliminate the need for secure infrastructure.

---

# 32. Secret Management

Development:

```text
.env
local secret store
```

Production:

```text
AWS Secrets Manager
IAM roles
short-lived credentials where supported
```

Secrets must never be committed to Git.

---

# 33. CI/CD

GitHub Actions is the candidate CI/CD platform.

Pull request pipeline:

```text
Lint
 ↓
Unit Tests
 ↓
Data Contract Validation
 ↓
dbt Tests
 ↓
Infrastructure Validation
 ↓
Build
```

Deployment:

```text
Merge
 ↓
Build Artifact
 ↓
Deploy Staging
 ↓
Integration Tests
 ↓
Approval
 ↓
Deploy Production
```

Production deployments must be reproducible.

---

# 34. Infrastructure as Code

Terraform should define cloud infrastructure where appropriate.

Managed resources may include:

- S3
- IAM
- Glue
- Athena
- CloudWatch
- Secrets Manager
- Networking components

Infrastructure changes must pass validation before deployment.

---

# 35. Local Development

Local development should reproduce the logical platform as closely as practical.

Candidate Docker Compose services:

```text
Airflow
PostgreSQL
MinIO
Spark
dbt
```

DuckDB may operate as a local analytical engine without requiring a persistent service.

Local development should allow engineers to:

- Run ingestion
- Inspect raw data
- Execute quality checks
- Run transformations
- Reproduce failures
- Execute tests

---

# 36. AWS Architecture

Production cloud architecture may use:

```text
External Sources
      ↓
Airflow / Managed Orchestration
      ↓
S3 Raw
      ↓
Glue / Spark
      ↓
S3 Bronze
      ↓
Glue / dbt-compatible transformations
      ↓
S3 Silver
      ↓
S3 Gold
      ↓
Athena / BI / API
```

Supporting services:

```text
IAM
Secrets Manager
CloudWatch
CloudTrail
Terraform
GitHub Actions
```

The final architecture must be sized according to actual workload.

---

# 37. Storage Strategy

Object storage should use partitioning aligned with common access patterns.

Potential partition dimensions:

```text
source
dataset
observation_year
observation_month
```

Partitioning must not be excessive.

The final partition strategy shall be based on observed data volume and query patterns.

---

# 38. File Formats

Preferred analytical formats:

- Parquet for columnar analytical data
- JSON where raw source payload is inherently JSON
- CSV only where source requires it

Compression should be selected according to workload.

---

# 39. Database Strategy

PostgreSQL is recommended for:

- Pipeline metadata
- Control tables
- Dataset registry
- Run history
- Configuration
- Operational state

It should not automatically become the primary storage for every historical dataset.

Large analytical data should remain in object storage/lakehouse storage where appropriate.

---

# 40. Data Product Serving

Initial serving options:

### Athena

For serverless analytical access.

### BI

For dashboards and reporting.

### API

A controlled API may be introduced for programmatic consumers after core data products stabilize.

Serving architecture must not compromise raw-data preservation.

---

# 41. Testing Strategy

Testing occurs at multiple levels.

## Unit Tests

Test connector and transformation logic.

## Contract Tests

Validate expected source and internal schemas.

## Data Tests

Validate data quality rules.

## Integration Tests

Validate source-to-product workflows.

## End-to-End Tests

Validate complete pipeline execution.

## Failure Tests

Simulate:

- Source unavailable
- Malformed response
- Schema change
- Duplicate records
- Missing periods
- Invalid values
- Partial ingestion

Failure testing is mandatory for critical pipelines.

---

# 42. Data Reconciliation

Where reliable independent totals exist, the platform should reconcile:

- Source totals
- Bronze totals
- Silver totals
- Gold totals

Unexpected discrepancies should be investigated.

Not every transformation will preserve row counts; reconciliation rules must therefore be dataset-specific.

---

# 43. Performance Requirements

Performance targets shall be established after profiling.

The platform should optimize:

- Incremental processing
- Partition pruning
- Columnar storage
- Predicate pushdown
- Avoidance of unnecessary full scans
- Appropriate file sizing
- Reusable curated datasets

No arbitrary SLA should be declared before workload measurement.

---

# 44. Cost Management

Cloud architecture must include cost controls.

Controls include:

- Object lifecycle policies
- Query monitoring
- Partition optimization
- Avoiding unnecessary scans
- Scheduled resource usage
- Environment shutdown policies
- Budget alerts
- Right-sized compute

Cost should be treated as an engineering metric.

---

# 45. Disaster Recovery

Recovery objectives shall be defined per service/data product.

The design should support:

- Immutable raw history
- Reproducible infrastructure
- Version-controlled transformations
- Recoverable metadata
- Backups
- Replay from source/raw data
- Documented recovery procedures

Target RPO/RTO values remain TBD until business criticality is established.

---

# 46. Incident Management

Every production incident should record:

```text
Incident ID
Start time
Detection time
Affected dataset
Severity
Impact
Root cause
Resolution
Recovery actions
Preventive actions
Owner
```

Post-incident reviews should focus on systemic improvements rather than blame.

---

# 47. Operational Runbooks

Runbooks should exist for:

- Failed ingestion
- Source outage
- Authentication failure
- Schema drift
- Quality failure
- Backfill
- Duplicate data
- Incorrect publication
- Pipeline rollback
- Data restoration

Each runbook should contain:

1. Detection
2. Diagnosis
3. Containment
4. Recovery
5. Validation
6. Communication
7. Prevention

---

# 48. Source Change Management

Sources must be monitored for:

- URL changes
- API changes
- Authentication changes
- Schema changes
- Definition changes
- Frequency changes
- Historical revisions

A detected breaking change should trigger controlled investigation before downstream publication.

---

# 49. Deployment Strategy

Production deployment should use:

```text
Feature branch
   ↓
Pull Request
   ↓
Automated checks
   ↓
Code review
   ↓
Staging
   ↓
Integration validation
   ↓
Production
```

Production changes should be traceable to a version-controlled change.

---

# 50. Data Retention

Retention shall be determined by:

- Business value
- Source terms
- Storage cost
- Historical requirements
- Compliance requirements

Raw source history should generally receive stronger retention protection than transient processing artifacts.

---

# 51. Access Model

Access should be role-based.

Example:

```text
Platform Admin
Data Engineer
Data Analyst
Data Scientist
Business Consumer
Read-only Auditor
```

Production write privileges should be restricted.

---

# 52. Repository Architecture

Recommended:

```text
FINDEX/
├── README.md
├── docs/
│   ├── product/
│   │   └── PRD.md
│   ├── technical/
│   │   └── TDD.md
│   ├── data/
│   │   ├── source_catalog.md
│   │   ├── data_dictionary.md
│   │   └── contracts/
│   ├── architecture/
│   │   └── decisions/
│   ├── governance/
│   └── operations/
│       └── runbooks/
├── ingestion/
├── transformation/
├── orchestration/
├── tests/
├── infrastructure/
├── scripts/
└── .github/
```

---

# 53. Architecture Decision Records

Material technical decisions shall be documented as ADRs.

Examples:

```text
ADR-001 — Why object storage is the primary historical storage layer
ADR-002 — Source ingestion interface
ADR-003 — Canonical data model strategy
ADR-004 — Orchestration technology
ADR-005 — Transformation framework
ADR-006 — Cloud deployment strategy
ADR-007 — Temporal/versioning model
```

Each ADR should state:

- Context
- Decision
- Alternatives
- Consequences
- Status

---

# 54. Technical Debt Management

Technical debt must be explicitly tracked.

Debt categories:

- Reliability
- Security
- Performance
- Maintainability
- Data quality
- Documentation
- Architecture

Critical technical debt should have an owner and remediation plan.

---

# 55. Engineering Standards

Production code should follow:

- Version control
- Code review
- Automated tests
- Linting
- Formatting
- Type checking where appropriate
- Structured logging
- Configuration separation
- Secret isolation
- Documentation

---

# 56. Definition of Done — Dataset

A dataset is production-ready only when:

- Source is approved
- Connector is implemented
- Raw preservation works
- Schema is documented
- Data contract exists
- Quality checks exist
- Failure behavior is defined
- Historical behavior is understood
- Silver model is validated
- Gold product is documented
- Lineage exists
- Monitoring exists
- Runbook exists
- Tests pass
- Deployment is reproducible

---

# 57. Definition of Done — Pipeline

A pipeline is production-ready only when:

- It is orchestrated
- It is idempotent
- It has retry policy
- It has failure classification
- It records operational metadata
- It emits metrics/logs
- It has alerts
- It supports controlled reruns
- It supports backfill where required
- It has automated tests
- It is version controlled
- It has an operational owner

---

# 58. Security Review Checklist

Before production:

- [ ] No secrets in repository
- [ ] IAM roles reviewed
- [ ] Production write permissions restricted
- [ ] Encryption enabled
- [ ] Logs enabled
- [ ] Secrets managed centrally
- [ ] Public exposure reviewed
- [ ] Network access reviewed
- [ ] Dependency vulnerabilities checked

---

# 59. Production Readiness Review

Before launch, engineering must verify:

### Architecture

- [ ] Architecture documented
- [ ] Failure paths documented
- [ ] Dependencies identified

### Data

- [ ] Data contracts complete
- [ ] Quality thresholds approved
- [ ] Historical behavior understood
- [ ] Lineage verified

### Operations

- [ ] Monitoring active
- [ ] Alerts tested
- [ ] Runbooks complete
- [ ] Recovery tested

### Security

- [ ] Access model approved
- [ ] Secrets secured
- [ ] Auditability verified

### Deployment

- [ ] Infrastructure reproducible
- [ ] CI/CD operational
- [ ] Rollback procedure tested

---

# 60. Open Technical Questions

These remain intentionally unresolved until source reconnaissance:

1. Which exact OJK datasets are accessible through stable structured interfaces?
2. Which BI datasets can be accessed through supported public mechanisms?
3. Which BPS datasets and API endpoints provide required historical coverage?
4. What are the actual update frequencies?
5. How frequently are historical values revised?
6. What are the real payload sizes?
7. What rate limits exist?
8. Which sources require authentication?
9. Which datasets share compatible dimensions?
10. Which canonical entities can be reliably mapped?
11. Does the initial workload justify Spark?
12. Which workloads justify managed AWS services?
13. What are realistic freshness and recovery targets?

These questions must be answered before final architecture freeze.

---

# 61. Architecture Freeze Criteria

The architecture shall not be considered final until:

- Source catalog is complete for Release 1
- Source access has been tested
- Data samples have been profiled
- Volume has been measured
- Refresh behavior is understood
- Historical/revision behavior is understood
- Data contracts have been drafted
- Quality rules have been identified
- Query patterns are known
- Cost assumptions have been validated

---

# 62. Recommended Initial Architecture

Subject to validation:

```text
                  OFFICIAL SOURCES
              ┌───────┬───────┬───────┐
              │       │       │       │
             OJK     BI      BPS    Others
              │       │       │       │
              └───────┴───────┴───────┘
                          │
                    Source Connectors
                          │
                          ▼
                    Object Storage
                         RAW
                          │
                          ▼
                       BRONZE
                          │
                     DQ GATES
                          │
                          ▼
                       SILVER
                          │
                  Business Modeling
                          │
                          ▼
                        GOLD
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Athena         BI          API
```

Control plane:

```text
Airflow
PostgreSQL
Metadata
Data Quality
Observability
Secrets
```

Infrastructure:

```text
Terraform
GitHub Actions
AWS
```

Local equivalent:

```text
Docker
MinIO
PostgreSQL
Airflow
Spark
dbt
DuckDB
```

---

# 63. Technical Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Source API unavailable | High | Retry, alternate approved source method |
| Schema drift | High | Contract validation and change detection |
| Historical revision | High | Version/effective-date strategy |
| Poor source quality | High | DQ gates and quarantine |
| Duplicate ingestion | High | Idempotency keys |
| Cloud cost growth | Medium | Budgeting and query controls |
| Over-engineering | Medium | Technology justified by workload |
| Weak lineage | High | Metadata and transformation tracking |
| Operational dependency on one engineer | High | Documentation and runbooks |
| Incorrect business definitions | High | Data ownership and glossary |

---

# 64. Engineering Operating Model

FINDEX should operate using clear ownership.

For every production dataset:

```text
Business Owner
      │
      ├── Definition
      └── Business Acceptance

Data Owner
      │
      ├── Quality
      └── Governance

Technical Owner
      │
      ├── Pipeline
      ├── Reliability
      └── Incident Response
```

Ownership should not be implicitly assigned to whoever wrote the pipeline.

---

# 65. Final Technical Position

FINDEX is architected as a layered, governed data platform rather than a collection of independent ETL scripts.

The architecture separates:

- Source acquisition
- Raw preservation
- Source-aligned processing
- Standardization
- Business data products
- Serving
- Governance
- Operations

The platform must be capable of answering both:

> **“What data do we have?”**

and:

> **“Can we trust this data, where did it come from, what happened to it, and can we reproduce how it was produced?”**

The architecture is deliberately designed to evolve after source profiling rather than assuming that technology choices are the starting point.

---

# 66. Document Status

This TDD is an architecture baseline.

The following artifacts are required before implementation proceeds to production-grade development:

1. `source_catalog.md`
2. Data profiling reports
3. Initial data contracts
4. Architecture Decision Records
5. Detailed schema specifications
6. Environment/infrastructure design
7. Operational runbooks

Any material architectural change must be recorded through an ADR.
