# ADR-006 — Cloud Deployment Strategy

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §40 (deployment), §54 (infrastructure), §55 (release), §57 (CI/CD), §65 (security), §67 (runbooks), §69 (load testing), §71 (product readiness), §72 (cost management), §73 (technical debt), §74 (DR), §75 (logging), §78 (engineering), §80 (code review), §84 (security checklist), §86 (incident), §88 (architecture freeze), §94 (audit)...  

---

## Context

KLIBRA requires a cloud deployment that:

- Reproducible via IaC (TDD §34).
- Securely isolate environments (PRD §53, §65).
- Cost‑effective for academic/pilot workload (PRD §72).
- Support local development parity (TDD §35).
- Managed services justified by measured workload (TDD §94).

---

## Decision

Use **AWS as primary cloud** with selective managed services:

| Capability | Service | Justification |
| --- | --- | --- |
| Object Storage | S3 (with lifecycle policies) | Durable, scalable, raw/archive |
| Compute | EC2 or ECS for Airflow (or MWAA) | Orchestrated batch jobs |
| Compute | EMR or SageMaker Studio (Spark) | Distributed processing when needed |
| Database | RDS PostgreSQL (small) | Metadata, pipeline state |
| Analytics | Athena (serverless) | Querying data in S3 |
| Monitoring | CloudWatch / OpenTelemetry | Platform & data observability |
| Secrets | Secrets Manager | Credential isolation |
| IaC | Terraform | Reproducible infra |

Local dev uses Docker Compose with MinIO (S3‑compatible), PostgreSQL, Airflow, Spark, dbt, DuckDB.

---

## Alternatives Considered

- **Full Managed (Databricks + Redshift)** – Rejected: over‑engineered for current scale.
- **Selective Managed (selected)** – Balanced cost & capability.
- **Multi‑Cloud** – Rejected: premature complexity.
- **On‑Prem Only** – Rejected: limited scalability, operational overhead.

---

## Implementation Details

- All infra defined in `infrastructure/terraform/`.
- Environments: Dev, Staging, Prod (PRD §51, §53).
- CI/CD via GitHub Actions (ADR‑012). Deployment: merge → build → deploy Staging → integration tests → approval → deploy Prod.
- Secrets never in code (PRD §65, §78). Key rotation via Secrets Manager.
- Cost monitoring via AWS Cost Explorer + budget alerts (PRD §72, §97).

---

## Consequences

**Positive:**

- Reproducible infra, easy env creation/teardown.
- Cost visibility via AWS billing.
- Managed Airflow reduces ops overhead.
- Local dev parity via Docker + MinIO.

**Negative:**

- AWS‑specific lock‑in (mitigated by using open standards where possible).
- Initial learning curve for Terraform.

---

## Definition of Done

- Terraform modules for S3, RDS, EC2/ECS/MWAA, Athena, CloudWatch, Secrets Manager created and validated.
- Local dev stack (Docker Compose) fully functional with MinIO, PostgreSQL, Airflow, dbt, DuckDB.
- CI/CD pipeline (GitHub Actions) runs `terraform validate`, `terraform plan` on PRs.
- Documentation updated in `docs/operations/environment_management.md`, `docs/governance/access_review_process.md`.
- Security checklist (PRD §84) verified for staging and production.
- Sign‑off from Platform Admin and Data Governance.
