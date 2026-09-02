# Runbook — Duplicate Data

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for detecting, investigating, resolving, and preventing duplicate data in the FINDEX platform.

---

## 2. Detection

- Duplicate rate quality check exceeds threshold (0% for key fields)
- Monitoring alert for unexpected record count increase
- Idempotency key collision detected
- Downstream consumers report inconsistent counts

---

## 3. Diagnosis

### 3.1 Identify Duplicate Type

| Duplicate Type | Indicators |
|---|---|
| **Re-ingestion without idempotency** | Same source_version ingested twice |
| **Pipeline rerun without idempotency** | Same pipeline run produces duplicates |
| **Source duplication** | Source publishes identical data in multiple records |
| **Transformation duplication** | Transformation logic produces duplicates |
| **Join duplication** | Join logic creates unintended row multiplication |

### 3.2 Root Cause Analysis

1. Check idempotency key definition and implementation
2. Review pipeline run history for duplicate runs
3. Check if connector fetched same payload twice
4. Review transformation logic for cartesian product risks
5. Verify deduplication logic is functioning

---

## 4. Containment

1. Halt further ingestion for affected dataset
2. Identify the scope of duplication (how many duplicates, which periods)
3. Quarantine duplicate records if not yet published
4. Alert Technical Owner and Data Owner
5. Document in incident management system

---

## 5. Resolution

### 5.1 Removal

1. Identify duplicates using idempotency key (source_id, dataset_id, source_period, source_version, payload_hash)
2. Remove duplicate records, keeping the first occurrence
3. Verify deduplication is complete
4. Validate quality checks pass

### 5.2 Idempotency Fix

1. Fix idempotency key implementation
2. Update connector to properly use idempotency key
3. Test idempotency in staging
4. Rerun pipeline with fixed logic
5. Verify no new duplicates

### 5.3 Source-Side Resolution

If source publishes duplicates:
1. Implement deduplication in connector
2. Document source duplication pattern
3. Notify source institution if appropriate
4. Update quality checks to detect source-side duplicates

---

## 6. Validation

1. Verify duplicate rate is 0% for key fields
2. Verify record count matches expected
3. Run quality checks
4. Confirm downstream data products are consistent
5. Validate lineage is intact

---

## 7. Communication

- Alert Technical Owner immediately
- Notify Data Owner if duplicates affected published data
- Notify Business Owner if published data was affected
- Document in change log

---

## 8. Prevention

1. Ensure idempotency keys are properly implemented and tested
2. Add duplicate rate monitoring and alerting
3. Test connector with simulated duplicate payloads
4. Add failure test for duplicate scenarios
5. Implement deduplication at Bronze layer as safety net

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*