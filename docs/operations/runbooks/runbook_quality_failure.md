# Runbook — Quality Failure

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for responding when data quality checks fail during the FINDEX pipeline.

---

## 2. Detection

- Automated quality check failure alert
- Quality status shows QUARANTINED or REJECTED
- Quality score below threshold
- Data observability dashboard shows anomaly

---

## 3. Diagnosis

### 3.1 Identify Failure Scope

1. Determine severity (P0, P1, P2, P3)
2. Identify which quality rule(s) failed
3. Determine affected records, batch, or dataset
4. Assess if failure is systematic or isolated
5. Review quality metadata and error details

### 3.2 Root Cause Analysis

- Check source data for anomalies
- Verify transformation logic is correct
- Check if source schema or values changed
- Review if data contract thresholds are appropriate
- Identify if issue is source-side or FINDEX-side

---

## 4. Containment

1. Quarantine failing records or entire batch per severity
2. Prevent publication of failing data to downstream layers
3. Alert stakeholders based on severity
4. Document failure in incident management system
5. If P0: halt all publications from affected dataset

---

## 5. Resolution

### 5.1 Source Data Issue

1. Investigate source data quality
2. Contact source institution if data appears incorrect
3. Evaluate if issue is temporary or persistent
4. If temporary: retry when source data improves
5. If persistent: adjust quality thresholds or accept with warning

### 5.2 FINDEX Transformation Issue

1. Fix transformation logic
2. Update transformation code in staging
3. Revalidate with test data
4. Rerun pipeline with corrected logic
5. Validate quality checks pass

### 5.3 Threshold Issue

1. Evaluate if threshold is too strict or inappropriate
2. Propose threshold adjustment via change management
3. If urgent: apply temporary threshold adjustment with approval
4. Document threshold change
5. Revalidate with historical data

### 5.4 Quarantine Resolution

1. After root cause is identified and fixed
2. Reprocess quarantined records
3. Validate quality checks pass
4. Move records from quarantine to bronze/silver/gold
5. Update lineage and metadata
6. Document resolution

---

## 6. Validation

1. Verify quality checks pass on reprocessed data
2. Confirm quality score meets threshold
3. Run spot-check queries on published data
4. Verify no data was lost during quarantine
5. Confirm lineage is intact
6. Validate downstream data products are consistent

---

## 7. Communication

| Severity | Recipients | Response Time |
|---|---|---|
| P0 | Technical Owner, Data Owner, Data Governance, Executive | Immediate |
| P1 | Technical Owner, Data Owner, Business Owner | Within 4 hours |
| P2 | Technical Owner, Data Owner | Within 24 hours |
| P3 | Technical Owner | Weekly review |

Communication includes:
- Quality rule that failed
- Number and percentage of affected records
- Root cause
- Resolution action taken
- Preventive measures

---

## 8. Prevention

1. Refine quality rules based on findings
2. Add new quality checks if gap identified
3. Improve source data validation
4. Enhance monitoring and early detection
5. Update data contracts if thresholds need adjustment
6. Add quality tests for edge cases

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*