# ADR-005 — Transformation Framework

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §11 (Silver/Gold modelling); TDD §24 (transformation architecture), §63 (semantic metrics)  

---

## Context

KLIBRA requires transformations at three stages:

- **Raw → Bronze:** source‑specific parsing and error handling.
- **Bronze → Silver:** standardization to the canonical model (units, identifiers, temporal types).
- **Silver → Gold:** business‑oriented aggregations and Gold data products (PRD §11).

Each stage has different performance and language needs.

---

## Decision

Adopt a **multi‑framework architecture**:

- **Python** – for API clients, file extraction, source‑specific parsing, and lightweight joining/aggregation where Pandas suffices.
- **Apache Spark** – for distributed, large‑scale processing (e.g., historical backfills covering many years) where volume justifies cluster overhead.
- **dbt (data build tool)** – for SQL‑based, version‑controlled transformations, tests, and documentation (always used for Silver & Gold).
- **DuckDB** – for local analytical validation and ad‑hoc inspection.

---

## Framework Responsibilities

| Framework | Responsibility | When Used |
| --- | --- | --- |
| **Python** | API clients, extraction, parsing, procedural logic, small‑scale joins | Always |
| **Spark** | Distributed transformation, large historical processing, heavy aggregations | When volume warrants |
| **dbt** | SQL transformations, tests, docs, dependency graphs; mandatory for Silver/Gold | Always for Silver/Gold |
| **DuckDB** | Local validation, dev, ad‑hoc inspection, profiling | Development only |

---

## Implementation Details

- **Connector packages** (Python) reside under `ingestion/` and are tested via `tests/connector/`.
- **Spark jobs** reside under `transformation/batch/` and are invoked via `spark-submit` tasks in Airflow.
- **dbt project** located at `transformation/dbt/` defines models under `models/silver/` and `models/gold/` with accompanying tests (`tests` blocks) and documentation (`docs`).
- **DuckDB** usage documented in `docs/technical/TDD.md` §35 and local development guide.

---

## Consequences

**Positive:**

- Flexibility to choose the right tool per stage.
- Clear ownership: Python for per‑source ingestion, Spark for heavy lifting, dbt for governed Silver/Gold SQL.
- Strong testing and documentation via dbt.

**Negative:**

- Multiple languages / tooling increases onboarding effort; mitigated by shared conventions and runbooks.
- Spark added overhead for small batch sizes; handled by conditionally skipping Spark when row count below threshold.

---

## Definition of Done

- Python connectors validated in staging.
- Spark job for historical backfill passes integration tests.
- dbt models for Silver and Gold pass `dbt test` and CI contract validation.
- DuckDB validation scripts included in `scripts/` for profiling.
- Documentation updated (`docs/operations/monitoring_alerts.md`, `docs/governance/quality_governance.md`).
- Review sign‑off from Data Engineering and Data Governance.
