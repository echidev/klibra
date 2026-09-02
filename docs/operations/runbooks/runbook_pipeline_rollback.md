# Runbook — Pipeline Rollback

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for rolling back a pipeline to a previous version when the current version produces incorrect results, introduces bugs, or causes operational issues.

---

## 2. Triggers

- Pipeline produces incorrect data after deployment
- Pipeline fails consistently after deployment
- New transformation logic introduces data quality issues
- Schema change causes downstream failures
- Security vulnerability discovered in pipeline code
- Performance degradation after deployment

---

## 3. Pre-Rollback Assessment

1. Identify the current pipeline version and the target rollback version
2. Assess what changed between versions
3. Determine scope of rollback (single dataset or multiple)
4. Evaluate impact on downstream data products
5. Verify that the target version has been validated and tested
6. Confirm rollback is approved by Data Owner and Technical Owner

---

## 4. Procedure

### 4.1 Preparation

1. Document current state: version, run status, affected datasets
2. Identify rollback target version with known good state
3. Prepare rollback environment in staging
4. Test rollback in staging first
5. Validate that rolled-back version produces correct data
6. Prepare communication for downstream consumers

### 4.2 Execution

1. Freeze new deployments for affected pipeline
2. Deploy rollback version following CI/CD pipeline
3. Rerun pipeline for affected periods
4. Monitor execution to completion
5. Verify idempotency (no duplicate records from rerun)

### 4.3 Post-Rollback Validation

1. Verify data quality is ACCEPTED
2. Verify record count matches expected historical baseline
3. Run reconciliation against source data
4. Verify downstream data products are correct
5. Confirm lineage is intact
6. Verify no data was lost or corrupted
7. Validate freshness is within SLA

---

## 5. Critical Rules

1. **Always test rollback in staging before production.**
2. **Never rollback without documented approval.**
3. **Preserve all version history and deployment records.**
4. **Rollback must maintain immutability of raw data.**
5. **Rollback must be observable and auditable.**

---

## 6. Communication

- Notify Technical Owner and Data Owner before rollback
- Notify Business Owner if published data is affected
- Notify downstream consumers if data products change
- Document rollback reason, target version, and results
- Update deployment log

---

## 7. Post-Rollback Actions

1. Investigate root cause of failure in new version
2. Fix issues before redeploying new version
3. Add tests for the root cause
4. Update deployment checklist
5. Document lessons learned
6. Schedule redeployment of fixed version when ready

---

## 8. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*