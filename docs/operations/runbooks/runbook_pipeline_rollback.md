# Runbook — Pipeline Rollback

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §57 (CI/CD), §76 (rollback); TDD §33 (pipeline), §49 (deployment)  

---

## 1. Purpose

Define the procedure for rolling back a KLIBRA pipeline to a previous stable version when a new deployment causes failures or data corruption.

---

## 2. Detection

- Airflow DAG failure after deployment.
- Quality‑gate P0/P1 violation on newly published data.
- Downstream consumer reports data anomalies.
- Monitoring alert indicating pipeline runtime spike or error surge.

---

## 3. Preparation

1. Identify the **failed deployment version** (Git tag / Docker image tag).
2. Determine the **last known good version** (previous tag).
3. Ensure the previous version's artifacts (container image, Terraform state) are available.
4. Notify Technical Owner, Data Owner, and Business Owner.
5. Create a rollback ticket in the issue tracker.

---

## 4. Rollback Steps

### 4.1 Staging Validation

1. Deploy the previous version to **staging** via CI/CD.
2. Run **integration tests** and **quality checks**.
3. Verify that all affected datasets pass P0/P1 checks.
4. Obtain **Data Owner sign‑off**.

### 4.2 Production Rollback

1. Trigger the **rollback deployment** in CI/CD (use `git revert` or checkout previous tag).
2. Apply the corresponding **Terraform plan** to revert infrastructure changes if any.
3. Deploy the previous container image to the production environment.
4. Re‑run the affected Airflow DAGs with the rolled‑back code.
5. Monitor for successful completion and absence of errors.

### 4-3 Post‑Rollback Validation

1. Verify **quality checks** (P0/P1) pass for all affected datasets.
2. Confirm **lineage** reflects the rolled‑back version.
3. Run downstream consumer acceptance tests.
4. Record the rollback event in the incident management system.

---

## 5. Communication

- Immediate alert to Technical Owner and Data Owner.
- Update stakeholders on rollback status and ETA.
- Notify downstream consumers once the rollback completes and data is stable.
- Document root cause and remediation steps for future prevention.

---

## 6. Post‑Rollback

1. Conduct a **post‑mortem** to understand why the deployment failed.
2. Update **Change Management Process** with findings.
3. Add regression tests if missing.
4. Review CI/CD pipeline for gaps (e.g., missing tests).
5. Close the rollback ticket after verification.

---

## 7. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; added staging validation and post‑mortem steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
