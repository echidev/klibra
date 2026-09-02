# FINDEX — Infrastructure Design

**Document Type:** Infrastructure Design  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Platform Engineering  
**Classification:** Internal  

---

## 1. Purpose

This document defines the infrastructure architecture for FINDEX production deployment on AWS, managed via Terraform. It specifies the cloud resources, networking, security, and deployment patterns required to operate the platform reliably and securely.

---

## 2. Overview

FINDEX production infrastructure uses AWS managed services where economically justified, with Terraform defining all infrastructure as code. The architecture supports the data lakehouse pattern with object storage (S3) as the primary storage layer.

---

## 3. AWS Architecture

```text
External Sources
      ↓
Airflow / Managed Orchestration (MWAA)
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

---

## 4. Core Services

### 4.1 Object Storage

| Resource | Purpose | Configuration |
|---|---|---|
| S3 Bucket (Raw) | Immutable raw source payloads | Versioning enabled; lifecycle policies |
| S3 Bucket (Bronze) | Source-aligned transformed data | Lifecycle policies |
| S3 Bucket (Silver) | Standardized analytical entities | Lifecycle policies |
| S3 Bucket (Gold) | Consumer-oriented data products | Lifecycle policies |
| S3 Bucket (Quarantine) | Failed records and batches | Versioning enabled; longer retention |
| S3 Bucket (Metadata) | Operational metadata | Lifecycle policies |

All buckets:
- Server-side encryption (SSE-S3 or SSE-KMS)
- Bucket policies enforcing least-privilege access
- Access logging enabled
- No public access
- Cross-region replication for critical buckets

### 4.2 Compute

| Resource | Purpose | Configuration |
|---|---|---|
| MWAA | Managed Airflow orchestration | Scheduled scaling |
| AWS Glue | Managed ETL processing | G.2X workers; auto-scaling |
| Athena | Serverless querying | Provisioned capacity |
| RDS PostgreSQL | Operational metadata | Multi-AZ; automated backups |

### 4.3 Security

| Resource | Purpose | Configuration |
|---|---|---|
| IAM | Access management | Least privilege; role-based |
| Secrets Manager | Secret storage | Automatic rotation |
| CloudWatch | Monitoring | Alarms and dashboards |
| CloudTrail | Audit logging | All API calls logged |
| VPC | Network isolation | Private subnets; NAT gateway |
| KMS | Encryption key management | Customer managed keys |

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

---

## 6. Networking

```text
VPC
├── Public Subnet
│   └── NAT Gateway
├── Private Subnet (Data)
│   ├── RDS PostgreSQL
│   └── Glue/Spark
└── Private Subnet (Management)
    ├── MWAA
    └── Monitoring
```

- All data services in private subnets
- No direct internet access for data services
- NAT Gateway for outbound updates
- Security groups restrict inter-service communication

---

## 7. Environment Configuration

| Component | Development | Staging | Production |
|---|---|---|---|
| Object Storage | MinIO | S3 | S3 |
| Database | Local PostgreSQL | RDS (small) | RDS (multi-AZ) |
| Orchestration | Local Airflow | MWAA (small) | MWAA (standard) |
| Processing | Local Spark | Glue (2 workers) | Glue (auto-scaling) |
| Query Engine | DuckDB | Athena | Athena |
| Secrets | .env | Secrets Manager | Secrets Manager |
| Monitoring | Basic | CloudWatch | CloudWatch |
| Terraform Backend | Local | S3 + DynamoDB | S3 + DynamoDB |

---

## 8. Cost Management

| Control | Implementation |
|---|---|
| Object lifecycle policies | Hot → Warm → Cold → Archive |
| Query monitoring | Athena query cost tracking |
| Partition optimization | Partition pruning enabled |
| Scheduled resources | Non-prod shutdown policies |
| Budget alerts | CloudWatch budget alerts |
| Right-sized compute | Regular instance type review |
| Glue job optimization | Worker type and count tuning |

---

## 9. High Availability

| Component | Strategy |
|---|---|
| RDS PostgreSQL | Multi-AZ deployment |
| S3 | Cross-region replication |
| MWAA | Managed HA by AWS |
| Secrets Manager | Multi-AZ by AWS |
| CloudWatch | AWS managed |
| Terraform State | S3 + DynamoDB locking |

---

## 10. Disaster Recovery

- Infrastructure reproducible via Terraform
- RDS automated backups with retention
- S3 cross-region replication
- Pipeline code in Git
- DR runbook defined in operations/runbooks

---

## 11. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*