# ADR-004 — Orchestration Technology

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §25 (pipeline orchestration); TDD §25 (Airflow orchestration)  

---

## Context

KLIBRA requires a robust, extensible orchestration engine to schedule, monitor, and retry complex multi‑step pipelines (discover → extract → raw validation → bronze → quality gate → silver → gold → publish). Requirements include DAG‑based dependencies, rich UI, retry semantics, and managed service options for production (PRD §25, TDD §25).

---

## Decision

Adopt **Apache Airflow** as the primary orchestration platform:

- **DAG‑based workflow definition** – matches KLIBRA’s pipeline stages.
- **Extensive operator ecosystem** – native S3, Postgres, Glue, Spark, dbt operators.
- **Built‑in retry, SLA, and timeout handling** – aligns with TDD §26, §31.
- **Managed offering (MWAA)** for production to reduce ops burden while preserving local Airflow for development (TDD §35).
- **Observability via Airflow UI and logs** – satisfies platform observability (PRD §59).

---

## Alternatives Considered

- **Prefect** – Rejected. Smaller community, fewer enterprise integrations.
- **Dagster** – Rejected. Newer, fewer production references.
- **Custom Scheduler** – Rejected. Reinvents features already provided by Airflow.

---

## Implementation Details

- **Development** uses a local Airflow instance via Docker Compose (`docker-compose.yml` includes Airflow, Postgres, MinIO, Spark, dbt).
- **Production** runs on **AWS Managed Workflows for Apache Airflow (MWAA)**, with DAGs stored in the `orchestration/` directory and version‑controlled.
- DAG definition located at `orchestration/dags/klibra_pipeline.py` follows the conceptual flow (see TDD §25):

```text
discover → extract → raw_validation → bronze → quality_gate → silver → silver_quality → gold → publish → notify
```

- Each task uses the **standard connector interface** (ADR‑002) and **idempotency keys** (TDD §15) to guarantee exactly‑once execution.
- **Branching** for optional steps (e.g., Spark for large volumes) is implemented using Airflow `BranchPythonOperator`.
- **SLAs** defined per task (e.g., extraction must complete within 30 min) and monitored via Airflow alerts.
- **Security**: Airflow runs under a dedicated IAM role with least‑privilege S3 and Secrets Manager permissions (PRD §16, TDD §31).

---

## Consequences

**Positive:**

- Unified, observable pipeline definition.
- Easy to extend with new tasks (e.g., additional backfill DAGs).
- Managed service reduces operational overhead.
- Consistent retry and failure handling (TDD §26).

**Negative:**

- Airflow operational expertise required; mitigated by managed MWAA.
- Potential cold‑start latency for large DAGs; mitigated by pre‑warming workers.

---

## Definition of Done

- Airflow DAG deployed and runnable in staging.
- All pipeline stages executed as per conceptual flow.
- Monitoring and alerting for task failures configured (see Monitoring & Alerts ADR‑008).
- Documentation added to `docs/operations/ci_cd_pipeline.md` and runbooks for failure handling.
- Sign‑off from Data Governance (access) and Technical Owner.
