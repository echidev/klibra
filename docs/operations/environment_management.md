# KLIBRA — Environment Management

**Document Type:** Environment Management  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §53 (envs), §57 (CI/CD), §74 (DR); TDD §35, §36, §44, §71  

---

## 1. Purpose

Define the environment strategy for KLIBRA, ensuring proper isolation, management, and promotion of changes across Development, Staging, and Production environments (PRD §53, TDD §35).

---

## 2. Environment Architecture

```text
Development
  ↓
Staging
  ↓
Production
```

---

## 3. Development Environment

### 3.1 Purpose

Used for local engineering, experimentation, and rapid iteration.

### 3.2 Characteristics

| Attribute | Value |
| --- | --- |
| **Data** | Subset of production data, synthetic data, or anonymized data |
| **Infrastructure** | Docker Compose (local) |
| **Services** | Airflow, PostgreSQL, MinIO, Spark, dbt, DuckDB |
| **Access** | Data Engineers |
| **Deployment** | Manual |

### 3.3 Capabilities

- Run ingestion pipelines.
- Inspect raw data.
- Execute quality checks.
- Run transformations.
- Reproduce failures.
- Execute tests.

Docker Compose services (`docker-compose.yml`): Airflow, PostgreSQL, MinIO, Spark, dbt.

---

## 4. Staging Environment

### 4.1 Purpose

Integration testing and production‑like validation.

### 4.2 Characteristics

| Attribute | Value |
| --- | --- |
| **Data** | Production‑like data (anonymized or subset) |
| **Infrastructure** | Mirrors production (scaled down if needed) |
| **Services** | Airflow (or MWAA), PostgreSQL, S3/MinIO, Spark, dbt |
| **Access** | Data Engineers, QA |
| **Deployment** | Automated via CI/CD |

### 4.3 Validation Activities

- Integration tests.
- Production‑like validation.
- Data contract verification.
- Performance benchmarking.
- User acceptance testing.
- Data Owner sign‑off.

---

## 5. Production Environment

### 5.1 Purpose

Contains trusted, published data products for downstream consumption.

### 5.2 Characteristics

| Attribute | Value |
| --- | --- |
| **Data** | Trusted published data |
| **Infrastructure** | Full AWS cloud infrastructure |
| **Services** | Managed Airflow (MWAA), RDS PostgreSQL, S3, Glue, Athena, CloudWatch, Secrets Manager |
| **Access** | Restricted (least privilege) |
| **Deployment** | Automated via CI/CD with approval gate |

### 5.3 Production Rules

1. Production data **must not** be modified manually through ad‑hoc engineering actions (PRD §20, §25).
2. All changes must flow through the CI/CD pipeline.
3. All changes must be version‑controlled and traceable.
4. Access is restricted to authorized services and personnel.
5. Monitoring and alerting are active at all times.
6. Backup and recovery procedures are tested regularly.
7. Deployment requires **Data Owner** sign‑off after successful staging validation.

---

## 6. Environment Isolation

### 6.1 Isolation Principles

| Principle | Implementation |
| --- | --- |
| **Network isolation** | Separate VPCs/subnets per environment |
| **Data isolation** | Separate S3 buckets and databases per environment |
| **Access isolation** | Separate IAM roles per environment |
| **Credential isolation** | Separate secrets per environment |
| **Service isolation** | Separate service instances per environment |

### 6.2 Promotion Flow

```text
Development
  ↓ (manual)
Staging
  ↓ (CI/CD automated)
Production
  ↓ (approval gate)
```

Code, configuration, and infrastructure can only promote forward. Rollbacks are documented and tracked.

---

## 7. Environment Configuration

### 7.1 Configuration Separation

All environment‑specific configuration is separated from code:

- Environment variables.
- Terraform variables.
- Secrets stored in Secrets Manager (prod) or `.env` files (dev).
- Configuration files per environment.

### 7.2 Configuration Matrix

| Configuration | Development | Staging | Production |
| --- | --- | --- | --- |
| Object Storage | MinIO | S3 | S3 |
| Database | Local PostgreSQL | RDS (small) | RDS (multi-AZ) |
| Orchestration | Local Airflow | MWAA (small) | MWAA (standard) |
| Processing | Local Spark | Glue (2 workers) | Glue (auto‑scaling) |
| Query Engine | DuckDB | Athena | Athena |
| Secrets | `.env` | Secrets Manager | Secrets Manager |
| Monitoring | Basic | CloudWatch | CloudWatch |

---

## 8. Environment Lifecycle

### 8.1 Creation

- Infrastructure defined in Terraform.
- Data seeded or restored.
- Access configured.
- Monitoring enabled.
- Documentation updated.

### 8.2 Decommissioning

- Secure data deletion.
- Infrastructure destroyed via Terraform.
- Access revoked.
- Configuration archived.
- Documentation updated.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; updated environment matrix; added isolation principles; clarified production write restrictions |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
