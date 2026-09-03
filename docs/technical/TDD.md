# KLIBRA — Technical Design Document

**Document Type:** Technical Design Document (TDD)  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Architecture Baseline / Subject to Source Validation  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  

---

# 1. Purpose

This document defines the technical architecture, engineering standards, operational model, and implementation approach for KLIBRA.

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
         World Bank    IMF        FRED     ECB / Market APIs
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

Technology shall be selected by workload and operational evidence.

| Capability | Candidate Technology | Purpose |
| --- | --- | --- |
| Object Storage | S3 / MinIO | Durable raw and analytical storage |
| Table Format | Apache Iceberg | Schema evolution, snapshots, time travel where justified |
| Relational Metadata | PostgreSQL | Control plane, run state, registry |
| Orchestration | Apache Airflow | Scheduling and dependency management |
| Processing | Python / DuckDB / Spark | Source parsing, analytical transforms, scalable processing when required |
| SQL Transformation | dbt | Gold models, tests, documentation |
| Semantic Layer | dbt Semantic Layer / MetricFlow | Governed metrics and semantic relationships |
| Data Quality | OpenMetadata checks and/or Soda/Great Expectations | Automated quality controls |
| Data Catalog | OpenMetadata | Discovery, ownership, lineage, quality visibility |
| Local Analytics | DuckDB | Fast local inspection and validation |
| Containerization | Docker | Reproducible environments |
| CI/CD | GitHub Actions | Automated validation and deployment |
| IaC | Terraform | Reproducible cloud infrastructure |
| Cloud Analytics | Athena / Trino | SQL analytics on object storage |
| Monitoring | OpenTelemetry / CloudWatch | Platform and pipeline observability |
| Secrets | AWS Secrets Manager / environment secret store | Secret isolation |

Spark is optional and shall be justified by measured workload volume rather than included merely for architectural appearance.

OpenMetadata is preferred for catalog/lineage/quality because it provides dataset discovery, lineage relationships, column-level lineage, and data-quality workflows.

The semantic layer must remain conceptually independent from any single BI tool.

# 5. Environment Architecture

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
gold_macro_indicators
gold_interest_rate_monitor
gold_market_overview
gold_country_benchmark
```

Gold models should optimize for consumer usability rather than source fidelity.

---

# 11. Canonical Data Model

The platform should use a canonical observation model where compatible sources permit.

Conceptual structure:

```text
fact_economic_observation
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
      └── When KLIBRA acquired it
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

1. Official public API / SDMX service.
2. Official public bulk dataset.
3. Official public catalog/resource endpoint.
4. Official web source only where necessary, permitted, and testable.

KLIBRA shall not use institutional-only APIs for Release 1.

## 13.3 Source Access Classes

### Class A — Public, No Key

Example target: World Bank Indicators API; ECB Data Portal service.

### Class B — Public Self-Service Credential

Example target: FRED, Alpha Vantage, CoinGecko Demo API.

Credentials are obtained by the individual developer through provider self-service registration, never by institutional proposal.

### Class C — Public Statistical API with Portal/Account Considerations

Example target: IMF Data APIs. The API exposes SDMX programmatic access; portal tooling may require an account. This class is permitted only after a live endpoint test proves the required dataset is accessible with personal access and without an institutional approval process.

Scraping is a controlled fallback, not the default ingestion method..

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

KLIBRA requires two categories of observability.

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
KLIBRA/
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

# 60. Source Catalog & Accessibility Baseline

Release 1 source selection is constrained by personal reproducibility.

| Source | Primary Data | Access | Release 1 Role | Notes |
| --- | --- | --- | --- | --- |
| World Bank Indicators API | Development/macro indicators | Class A | Core | V2 API, no API key required |
| IMF Data API | Macro / balance of payments / statistics | Class C | Core/optional | SDMX 2.1/3.0; validate portal/account path |
| FRED | Macro/interest-rate series | Class B | Core | Personal API key required |
| ECB Data Portal | FX/monetary/statistical series | Class A | Core | SDMX REST service |
| Alpha Vantage | Market/FX/commodities | Class B | Optional market source | Free key and usage limits |
| CoinGecko Demo | Crypto market data | Class B | Optional alternative source | Demo key required |

The exact series list is versioned in `source_catalog.md` and must include endpoint-level verification timestamps.

World Bank's Indicators API provides programmatic access to nearly 16,000 time-series indicators and explicitly states that API keys/authentication are no longer necessary.

ECB's Data Portal provides an SDMX 2.1 RESTful web service for programmatic data and metadata access, including `updatedAfter` and historical version capabilities.

FRED requires a registered API key for web-service requests, using a self-service developer account rather than institutional proposal access.

Alpha Vantage provides a self-service free API key and documents broad categories including equities, FX, commodities, crypto, and economic indicators.

CoinGecko documents a free Demo API plan with a generated API key and direct API request workflow.

# 61. Public Source Connector Contract

Every connector shall expose a common interface conceptually equivalent to:

```text
discover()
validate_access()
extract()
validate_response()
normalize_envelope()
persist_raw()
emit_metadata()
```

`validate_access()` is mandatory for KLIBRA because reproducible personal deployment is a product constraint.

The connector must fail clearly when credentials, access rights, provider availability, or required endpoint capabilities are not satisfied.

# 62. Semantic Layer Architecture

The semantic layer sits above Gold and below consumer-specific presentation.

```text
Gold Data Products
       │
       ▼
Semantic Models
       │
       ├── Dimensions
       ├── Measures
       ├── Metrics
       ├── Time semantics
       └── Business definitions
       │
       ▼
Intelligence Models
       │
       ├── Composite scores
       ├── Signals
       ├── Coverage/confidence
       └── Explanations
       │
       ▼
BI / API / SQL / DS
```

Semantic definitions shall not contain source-ingestion logic.

## 61.1 Metric Grain

Every metric must declare its grain. Example:

```text
(country, indicator, observation_period)
```

## 61.2 Time Aggregation

Every metric must specify whether aggregation is:

- additive;
- average;
- end-of-period;
- latest-observation;
- weighted;
- non-aggregatable.

This prevents incorrect BI rollups.

## 61.3 Metric Versioning

Semantic metrics follow semantic versioning:

- MAJOR: meaning/formula incompatibly changed.
- MINOR: backward-compatible dimension or metadata enhancement.
- PATCH: documentation or non-semantic implementation fix.

# 63. Semantic Metric Registry

The metric registry should contain at least:

```text
metric_id
name
description
version
owner
grain
unit
formula
source_policy
aggregation_policy
time_semantics
quality_requirements
lineage_ref
effective_from
deprecation_status
```

Initial metric set:

- `gdp_growth_rate`
- `inflation_rate`
- `unemployment_rate`
- `policy_rate`
- `real_policy_rate`
- `fx_return`
- `market_volatility`
- `debt_to_gdp`
- `economic_momentum_index`
- `inflation_pressure_index`
- `market_stress_index`
- `country_risk_score`

# 64. Intelligence Layer Design

Composite intelligence products must follow this pattern:

```text
Trusted Semantic Metrics
          ↓
Coverage Check
          ↓
Normalization
          ↓
Weighting
          ↓
Composite Score
          ↓
Confidence / Coverage
          ↓
Explanation Components
```

## 63.1 Example — Economic Momentum Index

Candidate inputs:

- GDP growth.
- Industrial activity proxy where available.
- Employment/unemployment trend.

The methodology shall be explicit and version controlled.

## 63.2 Example — Inflation Pressure Index

Candidate inputs:

- Inflation trend.
- Producer-price proxy where available.
- Policy rate / real-rate context.

## 63.3 Example — Market Stress Index

Candidate inputs may include:

- Equity volatility proxy.
- FX volatility.
- Yield-spread proxy.

No composite index shall be published without sufficient component coverage.

# 65. Intelligence Score Data Model

Recommended model:

```text
fact_intelligence_score
------------------------
score_id
metric_id
entity_id
observation_period
score
score_band
confidence
coverage_ratio
methodology_version
input_snapshot_id
calculated_at
quality_status
```

Supporting table:

```text
fact_intelligence_component
----------------------------
score_id
component_metric_id
component_value
normalized_value
weight
contribution
quality_status
```

This structure enables explainability and reproducibility.

# 66. Data Contract Implementation

Contracts should be stored in the repository:

```text
docs/data/contracts/
    sources/
    bronze/
    silver/
    gold/
    semantic/
    intelligence/
```

A contract change must execute compatibility validation in CI.

Example contract skeleton:

```yaml
dataset: gold_macro_indicators
version: 1.2.0
owner: klibra-data-platform
grain:
  - entity_id
  - metric_id
  - observation_date
fields:
  entity_id:
    type: string
    nullable: false
  metric_id:
    type: string
    nullable: false
  observation_date:
    type: date
    nullable: false
  value:
    type: decimal
    nullable: true
quality:
  freshness_hours: 48
  duplicate_rate_max: 0
```

# 67. Data Quality Implementation Standard

Quality checks shall be mapped to contract severity.

```text
Contract
   ↓
DQ Rules
   ├── Error → Quarantine/Block
   ├── Warning → Publish with warning
   └── Pass → Continue
```

Minimum checks per production dataset:

- Schema.
- Primary/business key uniqueness.
- Nullability.
- Type validity.
- Domain/range validity.
- Date validity.
- Freshness.
- Duplicate detection.
- Row-count anomaly.
- Referential integrity where applicable.

# 68. Data Observability Model

KLIBRA shall expose two complementary planes.

## 67.1 Pipeline Plane

Metrics:

- Run duration.
- Task retries.
- Failure rate.
- API latency.
- API response codes.
- Records received.
- Records written.
- Compute usage.

## 67.2 Data Plane

Metrics:

- Freshness lag.
- Row count.
- Null rate.
- Duplicate rate.
- Distribution drift.
- Missing periods.
- Schema drift.
- Quality score.
- Coverage ratio.

OpenMetadata can act as a catalog and quality visibility layer; its current documentation covers table/column quality tests, alerts, profiler signals, and lineage including column-level mappings.

# 69. Data Lineage Standard

Lineage must represent:

```text
Provider Endpoint
      ↓
Raw Object
      ↓
Bronze Model
      ↓
Silver Model
      ↓
Gold Product
      ↓
Semantic Metric
      ↓
Intelligence Product
      ↓
Consumer
```

Where practical, lineage must also capture:

- Connector version.
- Transformation version.
- Pipeline run ID.
- Source payload hash.
- Semantic metric version.
- Intelligence methodology version.

# 70. Source Revision & Point-in-Time Strategy

KLIBRA shall distinguish:

- observation_time;
- source_publication_time;
- source_updated_time;
- ingestion_time;
- processing_time;
- effective_from;
- effective_to;
- source_version;
- payload_hash.

When source history is available, the connector should preserve revised versions instead of destructive overwrite.

ECB's service explicitly supports update detection through `updatedAfter` and historical data via `includeHistory`, making it an important design reference for revision-aware ingestion.

# 71. Idempotency Standard

Idempotency keys should be deterministic and dataset-specific.

Recommended default:

```text
hash(
  source_id,
  dataset_id,
  source_key,
  observation_period,
  source_version,
  payload_hash
)
```

A rerun of identical source evidence must not create duplicate published facts.

# 72. Incremental Extraction Standard

Connectors must choose the strongest available cursor:

1. Provider update cursor.
2. Provider update timestamp.
3. Publication timestamp.
4. Observation period.
5. Content hash.
6. Bounded/full refresh followed by deterministic dedupe.

Every connector must document why its selected cursor is reliable.

# 73. Rate-Limit & Provider Protection

Connectors shall implement:

- Retry with exponential backoff.
- Jitter.
- Request timeout.
- Connection pooling where safe.
- Respect for HTTP 429 semantics.
- Request caching where appropriate.
- Pagination safeguards.
- Maximum request budgets.
- Circuit-breaker behavior for repeated provider failure.

The orchestration layer must prevent retry storms.

# 74. Schema Drift Detection

Source payload schemas shall be fingerprinted.

A schema change shall be classified:

```text
Compatible
Potentially Breaking
Breaking
```

Breaking changes shall block downstream promotion until reviewed.

# 75. Consumer API Architecture

KLIBRA may expose a read-only API after Gold/semantic products stabilize.

Recommended API layers:

```text
/metrics
/metrics/{metric_id}
/countries
/intelligence
/intelligence/{product_id}
/metadata
/health
```

The serving API should query curated semantic/intelligence tables rather than raw source data.

The API shall expose provenance metadata where practical.

# 76. BI Architecture

BI tools shall consume semantic metrics rather than embedding critical formulas independently.

```text
BI Dashboard
     ↓
Semantic Metric
     ↓
Gold Model
     ↓
Silver / Raw lineage
```

Any dashboard-specific calculation must be classified as presentation logic, not authoritative business logic.

# 77. Notebook / Data Science Access

Data scientists may consume:

- Gold tables.
- Semantic extracts.
- Intelligence scores.
- Reproducible point-in-time snapshots.

Features derived from KLIBRA metrics must retain:

- metric version;
- source snapshot;
- calculation timestamp;
- feature code version.

# 78. Testing Pyramid

Testing shall include:

1. Connector unit tests.
2. Provider contract tests.
3. Data contract tests.
4. Transformation tests.
5. Data quality tests.
6. Semantic metric tests.
7. Intelligence methodology tests.
8. Integration tests.
9. End-to-end tests.
10. Failure-injection tests.

## 77.1 Intelligence Tests

Each composite metric must test:

- missing component;
- out-of-range component;
- zero coverage;
- duplicate component;
- version mismatch;
- weighting correctness;
- deterministic output.

# 79. CI/CD Quality Gates

Pull request:

```text
Format / Lint
      ↓
Unit Tests
      ↓
Contract Tests
      ↓
dbt Tests
      ↓
Semantic Metric Tests
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
Staging
  ↓
Integration Tests
  ↓
Data Contract Validation
  ↓
Approval
  ↓
Production
```

# 80. Repository Architecture

Recommended:

```text
KLIBRA/
├── README.md
├── docs/
│   ├── product/
│   │   └── PRD.md
│   ├── technical/
│   │   └── TDD.md
│   ├── data/
│   │   ├── source_catalog.md
│   │   ├── data_dictionary.md
│   │   ├── profiling/
│   │   └── contracts/
│   │       ├── sources/
│   │       ├── bronze/
│   │       ├── silver/
│   │       ├── gold/
│   │       ├── semantic/
│   │       └── intelligence/
│   ├── architecture/
│   │   └── decisions/
│   ├── governance/
│   └── operations/
│       └── runbooks/
├── ingestion/
│   ├── worldbank/
│   ├── imf/
│   ├── fred/
│   ├── ecb/
│   ├── alphavantage/
│   └── coingecko/
├── transformation/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── semantic/
├── intelligence/
├── orchestration/
├── tests/
├── infrastructure/
├── scripts/
└── .github/
```

# 81. Architecture Decision Records

Initial ADR set:

- ADR-001 — Why lakehouse/object storage is the primary historical layer.
- ADR-002 — Source connector interface.
- ADR-003 — Why Iceberg is/ is not required at current scale.
- ADR-004 — Orchestration technology.
- ADR-005 — Transformation framework.
- ADR-006 — Semantic layer technology.
- ADR-007 — Catalog and lineage technology.
- ADR-008 — Data quality framework.
- ADR-009 — Revision and point-in-time model.
- ADR-010 — Intelligence metric methodology.
- ADR-011 — Cloud versus local deployment.
- ADR-012 — Serving API boundary.

Each ADR shall contain:

- Context.
- Problem.
- Options.
- Decision.
- Consequences.
- Rollback/revisit trigger.
- Status.

# 82. Disaster Recovery & Replay

KLIBRA shall favor replayable recovery rather than manual editing.

Recovery sequence:

```text
Infrastructure Recovery
        ↓
Metadata Recovery
        ↓
Raw Evidence Validation
        ↓
Bronze Replay
        ↓
Silver Replay
        ↓
Gold Validation
        ↓
Semantic Rebuild
        ↓
Intelligence Rebuild
```

Target RPO/RTO remain workload-specific but the platform must document recovery assumptions.

# 83. Operational Runbooks

Runbooks must exist for:

- API outage.
- Authentication failure.
- HTTP 429/rate limiting.
- Schema drift.
- Contract failure.
- DQ failure.
- Stale dataset.
- Duplicate ingestion.
- Backfill.
- Revision replay.
- Incorrect semantic metric.
- Incorrect intelligence score.
- Data restoration.
- Production rollback.

Every runbook must include:

1. Detection.
2. Diagnosis.
3. Containment.
4. Recovery.
5. Validation.
6. Communication.
7. Prevention.

# 84. Cost Management

Cost telemetry shall cover:

- Object storage.
- Query scans.
- Compute runtime.
- API request volume.
- Retry volume.
- Egress where applicable.

Optimization techniques:

- Partition pruning.
- Columnar Parquet.
- Incremental models.
- Request caching.
- Bounded date ranges.
- Appropriate file sizing.
- Lifecycle policies.
- Environment shutdown.

# 85. Security Review Checklist

Before production:

- [ ] No secrets in repository.
- [ ] IAM reviewed.
- [ ] Production write access restricted.
- [ ] Encryption enabled where supported.
- [ ] Audit logs enabled.
- [ ] API keys stored securely.
- [ ] Public exposure reviewed.
- [ ] Dependencies scanned.
- [ ] Provider terms reviewed.
- [ ] Source redistribution constraints documented.

# 86. Production Readiness Review

## Architecture

- [ ] Failure paths documented.
- [ ] Dependencies identified.
- [ ] ADRs complete.

## Sources

- [ ] Every source live-tested.
- [ ] Access class documented.
- [ ] Rate limits tested or bounded.
- [ ] Fallback strategy documented.

## Data

- [ ] Contracts complete.
- [ ] Quality thresholds approved.
- [ ] Temporal behavior understood.
- [ ] Revisions tested.
- [ ] Lineage verified.

## Semantic Layer

- [ ] Metric catalog complete.
- [ ] Formulas tested.
- [ ] Versioning policy implemented.
- [ ] Owners assigned.

## Intelligence

- [ ] Methodology documented.
- [ ] Component lineage available.
- [ ] Coverage/confidence implemented.
- [ ] Edge cases tested.

## Operations

- [ ] Monitoring active.
- [ ] Alerts tested.
- [ ] Runbooks complete.
- [ ] Recovery tested.

# 87. Technical Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Provider API unavailable | High | Retry, source fallback, cached evidence |
| Provider rate limiting | High | Backoff, budget, caching |
| API key revoked | High | Secret rotation, access validation |
| Schema drift | High | Contract validation |
| Historical revision | High | Version/effective-date model |
| Definition mismatch | High | Semantic source policy |
| Composite metric instability | High | Coverage thresholds and methodology versioning |
| Data quality degradation | High | DQ gates/quarantine |
| Duplicate ingestion | High | Idempotency keys |
| Cloud cost growth | Medium | Cost telemetry and query controls |
| Over-engineering | Medium | ADR and measured workload |
| Weak lineage | High | Catalog and metadata enforcement |
| Single-engineer dependency | High | Runbooks, contracts, documentation |
| Incorrect metric semantics | High | Semantic governance and tests |

# 88. Definition of Done — Source Connector

A connector is complete only when:

- Access is live-tested.
- Access class is documented.
- Credential handling is secure.
- Pagination is handled.
- Rate limiting is handled.
- Retry policy is implemented.
- Raw payload preservation works.
- Metadata is emitted.
- Idempotency is proven.
- Error classes are documented.
- Contract tests pass.
- Runbook exists.

# 89. Definition of Done — Semantic Metric

A metric is production-ready only when:

- Definition is approved.
- Grain is explicit.
- Formula is versioned.
- Dimensions are declared.
- Aggregation rules are defined.
- Source policy is documented.
- Data quality requirements are defined.
- Unit is explicit.
- Tests pass.
- Lineage exists.
- Owner is assigned.

# 90. Definition of Done — Intelligence Product

An intelligence product is production-ready only when:

- Methodology is documented.
- Inputs are versioned.
- Normalization is explicit.
- Weights are versioned.
- Coverage rules are defined.
- Confidence is exposed where applicable.
- Explainability is available.
- Historical behavior is tested.
- Lineage is complete.
- Business limitations are documented.

# 91. Final Technical Position

KLIBRA is intentionally architected as a governed economic intelligence platform rather than a set of independent ETL scripts.

The architecture separates:

- Source access.
- Raw evidence preservation.
- Source-aligned processing.
- Canonical standardization.
- Data products.
- Semantic metrics.
- Intelligence products.
- Serving.
- Governance.
- Observability.
- Operations.

The platform must be capable of answering:

> What data do we have? Can we trust it? Where did it come from? What changed? Which business definition produced this metric? Can we reproduce the intelligence score?

The architecture is designed to remain credible at portfolio scale while retaining a path to production-grade evolution.

# 92. Document Status

This TDD is the architecture baseline for KLIBRA v2.0.

Required implementation artifacts:

1. `source_catalog.md`
2. Data profiling reports
3. Initial source contracts
4. Gold data contracts
5. Semantic metric catalog
6. Intelligence methodology specifications
7. ADR set
8. Infrastructure/environment design
9. Operational runbooks
10. Production readiness review evidence

Any material architectural change must be documented through an ADR.

# 93. Open Technical Questions

These remain intentionally unresolved until source reconnaissance and workload measurement:

1. Which exact IMF datasets and endpoints are required for Release 1 and how will personal access be provisioned?
2. Which FRED series are selected as canonical policy/macro indicators?
3. Which Alpha Vantage market series are permitted under the chosen usage tier?
4. Which CoinGecko series are necessary, and does the free Demo tier satisfy the planned request budget?
5. Which source combinations are semantically comparable enough for reconciliation?
6. Which geographic crosswalk becomes canonical?
7. Does the initial workload justify Apache Iceberg or can Parquet datasets remain sufficient?
8. Does the initial workload justify Spark?
9. Which semantic serving mode is required first: dbt/SQL, API, or BI-native?
10. Which intelligence products have sufficient evidence and coverage to be published?
11. Which SLOs can be tightened after baseline measurement?
12. Which cloud services materially reduce operational burden without exceeding portfolio cost constraints?

These questions must be answered through experiments and ADRs, not assumptions.

# 94. Architecture Freeze Criteria

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

# 95. Recommended Initial Architecture

Subject to validation:

```text
                  OFFICIAL SOURCES
              ┌────────┬────────┬────────┬──────────────┐
              │        │        │        │              │
         World Bank   IMF     FRED      ECB       Market APIs
              │        │        │        │              │
              └────────┴────────┴────────┴──────────────┘
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

# 96. Technical Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
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

# 97. Engineering Operating Model

KLIBRA should operate using clear ownership.

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

# 98. Final Technical Position

KLIBRA is architected as a layered, governed data platform rather than a collection of independent ETL scripts.

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

# 99. Document Status

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

# Appendix A — External Technical References

- World Bank API: <https://datahelpdesk.worldbank.org/knowledgebase/articles/889392>
- IMF Data APIs: <https://data.imf.org/en/Resource-Pages/IMF-API>
- FRED API: <https://fred.stlouisfed.org/docs/api/>
- ECB SDMX API: <https://data.ecb.europa.eu/help/api/overview>
- Alpha Vantage: <https://www.alphavantage.co/documentation/>
- CoinGecko Demo API: <https://docs.coingecko.com/>
- OpenMetadata: <https://docs.open-metadata.org/>

Provider capabilities and quotas are subject to change. Endpoint availability must be revalidated before implementation and at each source onboarding event.
