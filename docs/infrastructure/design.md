# KLIBRA — Infrastructure Design

**Document Type:** Infrastructure Design  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §53 (envs), §54 (infrastructure), §57 (CI/CD), §60 (cost), §61 (security), §65 (monitoring), §72 (cost management), §78 (engineering), §86 (incident), §87 (monitoring), §91 (architecture freeze); TDD §3, §6, §34, §36, §44, §45, §46  

---

## 1. Purpose

Define the production infrastructure architecture for KLIBRA, managed via Terraform on AWS. Specifies the cloud resources, networking, security, cost, observability, and deployment patterns required to operate the platform reliably and securely (PRD §54, TDD §36).

---

## 2. Overview

KLIBRA uses AWS managed services where economically justified (ADR‑006), with Terraform defining all infrastructure as code. The architecture implements the data lakehouse pattern with object storage (S3) as the primary storage layer (ADR‑001).

---

## 3. AWS Architecture

```text
External Sources
      ↓
Airflow / MWAA (Orchestration)
      ↓
S3 Raw (immutable, lifecycle policies)
      ↓
Glue / Spark (Bronze transformation)
      ↓
S3 Bronze
      ↓
Glue / dbt-compatible transformations (Silver)
      ↓
S3 Silver
      ↓
Gold dbt models
      ↓
S3 Gold
      ↓
Athena (serverless query) / BI / Consumer API
```

Supporting services:

```text
RDS PostgreSQL  – metadata, pipeline state
Secrets Manager – secret storage with rotation
CloudWatch      – platform + data observability
CloudTrail      – audit logs
OpenMetadata    – data catalog and lineage
OpenTelemetry   – distributed tracing
```

---

## 4. Core Services

### 4.1 Object Storage

| Bucket | Purpose | Configuration |
| --- | --- | --- |
| `s3://klibra-data-raw` | Immutable raw source payloads | Versioning, lifecycle: Hot→Warm→Cold→Archive |
| `s3://klibra-data-bronze` | Source-aligned transformed data | Lifecycle policies |
| `s3://klibra-data-silver` | Standardized analytical entities | Lifecycle policies |
| `s3://klibra-data-gold` | Consumer-oriented data products | Lifecycle policies |
| `s3://klibra-data-quarantine` | Failed records and batches | Versioning, 90-day retention |
| `s3://klibra-data-metadata` | Operational metadata, manifests | Lifecycle policies |

All buckets:

- Server-side encryption (SSE‑KMS).
- Bucket policies enforcing least-privilege.
- Access logging enabled.
- No public access.
- Cross-region replication for Raw + Quarantine.

### 4.2 Compute

| Resource | Purpose | Configuration |
| --- | --- | --- |
| **MWAA** | Managed Airflow | Scheduled scaling, environment per stage |
| **AWS Glue (Spark)** | Managed ETL | G.2X workers, auto-scaling |
| **Athena** | Serverless querying | Provisioned capacity, workgroup per environment |
| **RDS PostgreSQL** | Operational metadata | Multi-AZ, automated backups |

### 4.3 Security

| Resource | Purpose | Configuration |
| --- | --- | --- |
| **IAM** | Access management | Least privilege, role-based |
| **Secrets Manager** | Secret storage | Automatic rotation |
| **CloudWatch** | Monitoring | Alarms, dashboards |
| **CloudTrail** | Audit logging | All API calls logged |
| **VPC** | Network isolation | Private subnets, NAT gateway |
| **KMS** | Encryption key management | Customer managed keys |

---

## 5. Terraform Structure

```text
infrastructure/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── networking/
│   ├── storage/
│   ├── compute/
│   ├── database/
│   ├── security/
│   ├── monitoring/
│   └── orchestration/
└── environments/
    ├── development/
    ├── staging/
    └── production/
```

### 5.1 Validation

All Terraform changes must pass:

```text
terraform fmt
terraform validate
terraform plan
Security review
Approval
Apply
```

CI integration: every PR runs `tflint` + `terraform validate` + `terraform plan` (PRD §57, TDD §33).

---

## 6. Networking

```text
VPC
├── Public Subnet
│   └── NAT Gateway
├── Private Subnet (Data)
│   ├── RDS PostgreSQL
│   └── Glue / Spark
└── Private Subnet (Management)
    ├── MWAA
    └── Monitoring
```

- All data services in private subnets.
- No direct internet access for data services.
- NAT Gateway for outbound updates.
- Security groups restrict inter-service communication.

---

## 7. Environment Configuration

| Component | Development | Staging | Production |
| --- | --- | --- | --- |
| Object Storage | MinIO | S3 | S3 |
| Database | Local PostgreSQL | RDS (small) | RDS (multi-AZ) |
| Orchestration | Local Airflow | MWAA (small) | MWAA (standard) |
| Processing | Local Spark | Glue (2 workers) | Glue (auto-scaling) |
| Query Engine | DuckDB | Athena | Athena |
| Secrets | .env | Secrets Manager | Secrets Manager |
| Monitoring | Basic | CloudWatch | CloudWatch |
| Catalog | OpenMetadata (local) | OpenMetadata (staging) | OpenMetadata (prod) |
| Terraform Backend | Local | S3 + DynamoDB | S3 + DynamoDB |

---

## 8. Cost Management

| Control | Implementation |
| --- | --- |
| Object lifecycle policies | Hot → Warm → Cold → Archive (ADR‑008) |
| Query monitoring | Athena query cost tracking, workgroup budgets |
| Partition optimization | Partition pruning + Iceberg (when justified) |
| Scheduled resources | Non-prod shutdown policies |
| Budget alerts | CloudWatch budget alerts |
| Right-sized compute | Regular instance type review |
| Glue job optimization | Worker type and count tuning |

Per PRD §72, cost is treated as a first-class engineering metric. Monthly cost review by Platform Admin.

---

## 9. High Availability

| Component | Strategy |
| --- | --- |
| RDS PostgreSQL | Multi-AZ deployment |
| S3 | Cross-region replication (Raw + Quarantine) |
| MWAA | Managed HA by AWS |
| Secrets Manager | Multi-AZ by AWS |
| CloudWatch | AWS managed |
| OpenMetadata | HA configuration (active-passive) |
| Terraform State | S3 + DynamoDB locking |

---

## 10. Disaster Recovery

- Infrastructure reproducible via Terraform (TDD §45).
- RDS automated backups with 30-day retention.
- S3 cross-region replication (Raw + Quarantine).
- Pipeline code in Git (zero data loss).
- DR runbook defined in `docs/operations/disaster_recovery.md`.

RPO/RTO targets per dataset defined in Disaster Recovery document.

---

## 11. Observability

| Layer | Tool | Purpose |
| --- | --- | --- |
| Platform | CloudWatch + OpenTelemetry | Infrastructure metrics, traces |
| Pipeline | Airflow UI + CloudWatch logs | Task duration, retries, failures |
| Data | OpenMetadata + custom probes | Freshness, quality, lineage |
| Alerting | CloudWatch Alarms + SNS | Severity-based routing |

Detailed metrics and thresholds in `docs/operations/monitoring_alerts.md`.

---

## 12. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re-aligned to KLIBRA PRD v2.0 / TDD v2.0; updated source list, bucket naming (`klibra-data-*`), added OpenMetadata, Athena workgroup budgets, cost/observability integration |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
