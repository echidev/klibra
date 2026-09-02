# Runbook — Data Restoration

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for restoring data in the FINDEX platform following data loss, corruption, or disaster events.

---

## 2. Detection

- Data loss detected through monitoring or audit
- Data corruption identified through quality checks
- Storage failure or data integrity issue
- Disaster event affecting production infrastructure
- Ingestion pipeline produces incorrect data that was published

---

## 3. Principles

1. **Raw data is immutable** — source payloads in Raw layer are preserved and serve as the ultimate source of truth.
2. **Infrastructure is reproducible** — Terraform-defined infrastructure can be recreated.
3. **Transformations are versioned** — transformation code is tracked in version control.
4. **Metadata is recoverable** — operational metadata is stored in PostgreSQL with backups.

---

## 4. Procedure

### 4.1 Assessment

1. Identify the scope of data loss or corruption
2. Determine affected layers (Raw, Bronze, Silver, Gold)
3. Identify affected time periods
4. Assess whether source data in Raw layer is intact
5. Determine RPO (Recovery Point Objective) and RTO (Recovery Time Objective)

### 4.2 Restoration from Raw Data

If Raw layer data is intact:

1. Verify Raw data integrity using content hashes
2. Re-run Bronze transformation on verified Raw data
3. Re-run Silver transformation on verified Bronze data
4. Re-run Gold transformation on verified Silver data
5. Validate each layer before proceeding to next
6. Publish corrected data to production

### 4.3 Full Infrastructure Restoration

If infrastructure is affected:

1. Deploy infrastructure from Terraform definitions
2. Restore PostgreSQL metadata from backup
3. Restore object storage from backup or cross-region replication
4. Re-deploy pipeline code from version control
5. Re-run pipeline for affected periods
6. Validate all layers

### 4.4 Point-in-Time Recovery

If point-in-time recovery is needed:

1. Identify the target point-in-time timestamp
2. Use effective_from/effective_to to reconstruct state at that point
3. Validate reconstructed data
4. Publish reconstructed data if required

---

## 5. Validation

1. Verify data integrity using content hashes
2. Run all quality checks
3. Verify record counts match historical baselines
4. Run reconciliation against source totals
5. Verify lineage is intact
6. Confirm downstream data products are correct
7. Validate freshness and temporal continuity

---

## 6. Communication

- Alert Technical Owner and Data Owner immediately
- Notify Business Owner for P0/P1 events
- Notify downstream consumers if published data is affected
- Document all restoration steps and results
- Provide recovery timeline to stakeholders
- Conduct post-incident review

---

## 7. Prevention

1. Maintain regular backups of PostgreSQL and object storage
2. Implement cross-region replication for critical data
3. Test restoration procedures regularly
4. Define and document RPO/RTO per service/data product
5. Monitor data integrity continuously
6. Maintain immutable raw data as ultimate backup

---

## 8. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*