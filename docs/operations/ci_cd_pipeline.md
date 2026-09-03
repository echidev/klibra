# KLIBRA — CI/CD Pipeline

**Document Type:** CI/CD Pipeline  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §40 (release), §57 (CI/CD), §78 (engineering); TDD §33, §79  

---

## 1. Purpose

Define the CI/CD pipeline strategy for KLIBRA, ensuring reproducible, automated validation and deployment of all platform changes (PRD §57, TDD §33, §79).

---

## 2. CI/CD Platform

GitHub Actions is the CI/CD platform.

---

## 3. Pull Request Pipeline

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
Intelligence Methodology Tests
  ↓
Infrastructure Validation (Terraform)
  ↓
Build
```

### 3.1 Format / Lint

- Python: `ruff` / `black` / `mypy` / `isort`.
- SQL (dbt): `sqlfluff`.
- Terraform: `tflint`, `terraform fmt -check`.
- YAML: `yamllint`.
- Markdown: documentation linter.

### 3.2 Unit Tests

- Connector unit tests.
- Transformation unit tests.
- Quality check unit tests.
- Metadata operation tests (idempotency keys, payload hash).

### 3.3 Contract Tests

- Source schema vs. contract.
- Internal schema (Bronze/Silver/Gold) vs. contract.
- Field type / nullability / range checks.
- Compatibility validation (semver).

### 3.4 dbt Tests

- dbt model tests.
- Freshness tests.
- Uniqueness tests.
- Not-null tests.
- Referential integrity tests.
- Custom data tests.

### 3.5 Semantic Metric Tests

- Formula evaluation vs. expected reference.
- Grain correctness.
- Time aggregation behavior.
- Source policy compliance.

### 3.6 Intelligence Methodology Tests

- Component coverage calculation.
- Weighting correctness.
- Deterministic output check.
- Edge case handling.

### 3.7 Infrastructure Validation

- `terraform validate` + `terraform plan`.
- Security group review.
- IAM policy validation.
- Cost estimation.

### 3.8 Build

- Container image build.
- Artifact creation.
- Version tagging.

---

## 4. Deployment Pipeline

```text
Merge → Build Artifact → Deploy Staging → Integration Tests
       → Data Contract Validation → Approval → Deploy Production
       → Post-Deployment Verification
```

### 4.1 Staging Deployment

- Deploy to staging environment.
- Run integration tests.
- Validate against staging data.
- Data Owner sign-off.

### 4.2 Integration Tests

- End-to-end pipeline execution.
- Data quality validation.
- API integration tests.
- Database migration tests.
- Performance benchmarks.

### 4.3 Approval Gate

- Code review approval required.
- Data Governance approval for breaking changes (per Change Management Process).
- Staging validation passed.
- All automated checks passed.
- Production deployment scheduled.

### 4.4 Production Deployment

- Reproducible deployment via Terraform + GitHub Actions.
- Blue-green or rolling deployment strategy.
- Monitoring active during deployment.
- Rollback plan prepared.
- Deployment logged and auditable.

---

## 5. Rollback Procedure

1. Identify rollback target version (last known-good release).
2. Deploy rollback version via CI/CD (revert tag).
3. Validate rollback in staging.
4. Deploy to production.
5. Verify data quality and pipeline health.
6. Document rollback reason and results.
7. Open incident if P0/P1 impact.

---

## 6. Environment Strategy

| Environment | Purpose | Deployment Trigger |
| --- | --- | --- |
| Development | Local engineering | Manual |
| Staging | Integration testing | Pull request merge |
| Production | Trusted published data | Approval after staging validation |

Production data must **not** be modified through ad-hoc engineering actions (PRD §20).

---

## 7. Artifact Management

| Artifact | Storage | Retention |
| --- | --- | --- |
| Container images | Container registry (ECR) | Per retention policy |
| Terraform plans | Artifact storage | Permanent |
| Pipeline logs | CloudWatch / GitHub Actions | Per retention policy |
| Build artifacts | Artifact storage (S3) | Per retention policy |
| dbt manifests | Object storage (`/metadata/`) | Permanent |

---

## 8. Security in CI/CD

- **No secrets** in repository (verified by secret scanner — `gitleaks`).
- IAM roles for GitHub Actions via OIDC.
- Short-lived credentials.
- Signed commits where supported.
- Branch protection rules.
- Required reviews before merge.
- Dependency scanning (`pip-audit`, `npm audit`, `safety`).

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re-aligned to KLIBRA PRD v2.0 / TDD v2.0; added semantic metric + intelligence methodology test gates |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
