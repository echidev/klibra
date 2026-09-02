# FINDEX — Environment Management

**Document Type:** Environment Management  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This document defines the environment strategy for FINDEX, ensuring proper isolation, management, and promotion of changes across development, staging, and production environments.

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

Used for local engineering and experimentation.

### 3.2 Characteristics

| Attribute | Value |
|---|---|
| **Data** | Subset of production data or synthetic data |
| **Infrastructure** | Docker Compose (local) |
| **Services** | Airflow, PostgreSQL, MinIO, Spark, dbt, DuckDB |
| **Access** | Data Engineers |
| **Deployment** | Manual |

### 3.3 Local Development Capabilities

Local development should allow engineers to:

- Run ingestion pipelines
- Inspect raw data
- Execute quality checks
- Run transformations
- Reproduce failures
- Execute tests

### 3.4 Docker Compose Services

```text
Airflow
PostgreSQL
MinIO
Spark
dbt
```

DuckDB operates as a local analytical engine without requiring a persistent service.

---

## 4. Staging Environment

### 4.1 Purpose

Used for integration testing and production-like validation.

### 4.2 Characteristics

| Attribute | Value |
|---|---|
| **Data** | Production-like data (anonymized or subset) |
| **Infrastructure** | Mirrors production (scaled down if needed) |
| **Services** | Airflow, PostgreSQL, S3/MinIO, Spark, dbt |
| **Access** | Data Engineers, QA |
| **Deployment** | Automated via CI/CD |

### 4.3 Validation Activities

- Integration tests
- Production-like validation
- Data contract verification
- Performance benchmarking
- User acceptance testing
- Data Owner sign-off

---

## 5. Production Environment

### 5.1 Purpose

Contains trusted published data products.

### 5.2 Characteristics

| Attribute | Value |
|---|---|
| **Data** | Trusted published data |
| **Infrastructure** | Full AWS cloud infrastructure |
| **Services** | Managed Airflow, PostgreSQL, S3, Glue, Athena, CloudWatch, Secrets Manager |
| **Access** | Restricted (least privilege) |
| **Deployment** | Automated via CI/CD with approval gate |

### 5.3 Production Rules

1. Production data must not be modified manually through ad-hoc engineering actions.
2. All changes must follow CI/CD pipeline.
3. All changes must be version-controlled and traceable.
4. Access is restricted to authorized services and personnel.
5. Monitoring and alerting are active at all times.
6. Backup and recovery procedures are tested.

---

## 6. Environment Isolation

### 6.1 Isolation Principles

| Principle | Implementation |
|---|---|
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

Code, configuration, and infrastructure can only promote forward through environments. Rollbacks are documented and tracked.

---

## 7. Environment Configuration

### 7.1 Configuration Separation

All environment-specific configuration is separated from code:

- Environment variables
- Terraform variables
- Secrets stored in Secrets Manager (production) or .env files (development)
- Configuration files per environment

### 7.2 Configuration Management

| Configuration | Development | Staging | Production |
|---|---|---|---|
| Object Storage | MinIO | S3 | S3 |
| Database | PostgreSQL | PostgreSQL | RDS PostgreSQL |
| Orchestration | Local Airflow | Managed Airflow | Managed Airflow |
| Processing | Local Spark | Spark/Glue | Spark/Glue |
| Query Engine | DuckDB | Athena | Athena |
| Secrets | .env | Secrets Manager | Secrets Manager |
| Monitoring | Basic | CloudWatch | CloudWatch |

---

## 8. Environment Lifecycle

### 8.1 Creation

New environments require:

1. Infrastructure defined in Terraform
2. Data seeded or restored
3. Access configured
4. Monitoring enabled
5. Documentation updated

### 8.2 Decommissioning

Decommissioned environments require:

1. Data securely deleted
2. Infrastructure destroyed via Terraform
3. Access revoked
4. Configuration archived
5. Documentation updated

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*