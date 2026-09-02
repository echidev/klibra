# ADR-006 — Cloud Deployment Strategy

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX must support both local development and production cloud deployment. The platform needs cloud services for scalable data processing, serverless querying, managed orchestration, and secure infrastructure. Cloud cost must remain controlled, and managed services should be justified by workload requirements.

---

## Decision

FINDEX shall use AWS as the primary cloud provider for production deployment, with the following managed services where economically justified:

- **S3** for object storage
- **RDS PostgreSQL** for operational metadata
- **Managed Airflow** (MWAA) for orchestration
- **AWS Glue** for managed ETL where justified
- **Athena** for serverless querying
- **CloudWatch** for monitoring
- **Secrets Manager** for secret management
- **Terraform** for Infrastructure as Code

Local development uses Docker Compose with MinIO (S3-compatible) and local PostgreSQL, Airflow, Spark, dbt, and DuckDB.

---

## Alternatives Considered

### Alternative A: Full Managed Services

Use all available managed AWS services.

| Aspect | Assessment |
|---|---|
| Pros | Minimal operational overhead; auto-scaling |
| Cons | Higher cost; vendor lock-in; may include unnecessary services |
| Verdict | **Rejected** — Use managed services only where justified by workload |

### B: Selective Managed Services (Selected)

Managed services where economically justified; self-managed where appropriate.

| Aspect | Assessment |
|---|---|
| Pros | Cost-effective; justified services only; flexibility to adjust |
| Cons | Mix of managed and self-managed requires careful management |
| Verdict | **Selected** — Aligns with TDD cost management principles |

### Alternative C: Multi-Cloud

Use multiple cloud providers.

| Aspect | Assessment |
|---|---|
| Pros | Avoids vendor lock-in; best-of-breed |
| Cons | Significant complexity; higher cost; more operational overhead |
| Verdict | **Rejected** — Premature for initial release |

### Alternative D: On-Premises Only

Self-hosted infrastructure without cloud.

| Aspect | Assessment |
|---|---|
| Pros | Full control; no cloud costs |
| Cons | Limited scalability; high operational overhead; no managed services |
| Verdict | **Rejected** |

---

## Consequences

### Positive

1. **Scalability** — Cloud scales with data and consumer growth
2. **Cost control** — Selective managed services; Terraform for infrastructure control
3. **Managed services** — Reduces operational burden for critical services
4. **Local parity** — Docker Compose enables full local reproduction
5. **Serverless options** — Athena and Glue reduce infrastructure management

### Negative

1. **Cloud costs** — Must be monitored and controlled (lifecycle policies, query monitoring, budget alerts)
2. **Vendor lock-in** — AWS-specific services; mitigated by Terraform and S3 compatibility
3. **Complexity** — Mix of managed and self-managed services

---

## Cost Management

Cloud architecture includes cost controls:

- Object lifecycle policies
- Query monitoring
- Partition optimization
- Avoiding unnecessary scans
- Scheduled resource usage
- Environment shutdown policies
- Budget alerts
- Right-sized compute

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | S3 as primary storage |
| ADR-002 | Connectors deployed in cloud |
| ADR-004 | Managed Airflow orchestration |
| ADR-008 | Storage tiering for cost management |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*