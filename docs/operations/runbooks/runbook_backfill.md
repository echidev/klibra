# Runbook — Backfill

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for executing backfill operations — explicit, controlled re-ingestion of historical data for a specified period.

Backfills must be explicit operations that never silently overwrite production history.

---

## 2. Triggers

- New source becomes available with historical data
- Source publishes historical corrections
- Connector or transformation fix requires reprocessing
- Data quality issues requiring historical correction
- Source system migration or data migration

---

## 3. Pre-Fill Requirements

Before initiating a backfill, the following must be specified:

| Requirement | Description |
|---|---|
| **Dataset** | Which dataset is being backfilled |
| **Start Period** | Earliest period to backfill |
| **End Period** | Latest period to backfill |
| **Reason** | Why the backfill is needed |
| **Requested By** | Who requested the backfill |
| **Code Version** | Version of connector/transformation to use |
| **Expected Impact** | Estimated record count and affected downstream products |
| **Validation Status** | How the backfill will be validated |
| **Approval** | Data Owner and Data Governance approval |

---

## 4. Procedure

### 4.1 Preparation

1. Obtain approval from Data Owner and Data Governance
2. Document backfill specification (start period, end period, reason, code version)
3. Freeze production pipeline for the affected dataset
4. Prepare backfill environment in staging
5. Verify backfill code version matches specification

### 4.2 Execution

1. Run backfill in staging first
2. Validate staging results:
   - Record count within expected range
   - Quality checks pass
   - No duplicate observations
   - Historical data is correct
3. Verify lineage is maintained
4. Compare backfilled data with existing production data

### 4.3 Production Deployment

1. Deploy backfill to production following CI/CD pipeline
2. Monitor execution to completion
3. Record backfill metadata (start time, end time, records processed, records rejected)
4. Do NOT overwrite existing production records; use effective_from/effective_to tracking
5. Preserve existing production history

### 4.4 Post-Fill Validation

1. Verify all periods in range are filled
2. Verify quality status is ACCEPTED or ACCEPTED_WARNING
3. Verify no duplicates with existing production data
4. Verify downstream data products are updated
5. Verify lineage is intact
6. Run reconciliation against source totals if available

---

## 5. Critical Rules

1. **Never silently overwrite production history.** All backfill records must have effective_from/effective_to tracking.
2. **Backfill must be documented.** Specification, approval, execution metadata, and results are all recorded.
3. **Backfill requires approval.** No backfill without documented approval from Data Owner and Data Governance.
4. **Backfill requires validation.** Staging validation before production deployment is mandatory.
5. **Backfill is observable.** All backfill operations are logged and auditable.

---

## 6. Rollback

If backfill produces incorrect results:

1. Halt backfill immediately
2. Identify the cause
3. Restore previous production data (preserved in immutable storage)
4. Re-run with corrected code if needed
5. Validate before resuming
6. Document the rollback and root cause

---

## 7. Communication

- Notify Data Owner and Business Owner before backfill begins
- Provide expected timeline and impact
- Notify after completion with results
- Document in change log

---

## 8. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*