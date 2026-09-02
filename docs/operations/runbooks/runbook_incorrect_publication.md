# Runbook — Incorrect Publication

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for responding when incorrect data has been published to production data products.

---

## 2. Detection

- Downstream consumer reports data anomaly
- Quality check identifies issue post-publication
- Data audit reveals unexpected values
- Data observability shows distribution anomaly
- Source data revision reveals published data was incorrect

---

## 3. Diagnosis

1. Identify the incorrect data and its scope
2. Determine root cause (source error, transformation error, quality gate failure)
3. Assess impact on downstream consumers
4. Identify all affected data products and periods
5. Calculate the volume and severity of incorrect data

---

## 4. Containment

1. Immediately halt further publication from affected dataset
2. Quarantine incorrect records if possible
3. Alert Technical Owner, Data Owner, and Business Owner
4. If P0: initiate emergency response protocol
5. Document in incident management system
6. Notify affected downstream consumers

---

## 5. Resolution

### 5.1 Rollback

1. Identify the last correct version of the data
2. Rollback to last known good version using immutable raw data
3. Validate rollback data quality
4. Republish corrected data
5. Verify downstream data products are updated

### 5.2 Re-ingestion and Re-publication

1. Fix root cause (connector, transformation, quality check)
2. Rerun pipeline for affected periods
3. Validate quality checks pass
4. Publish corrected data with effective_from/effective_to tracking
5. Preserve history of incorrect version for audit

### 5.3 Consumer Notification

1. Notify all affected consumers immediately
2. Provide details of incorrect data and correction
3. Provide corrected data access information
4. Document consumer acknowledgments

---

## 6. Validation

1. Verify corrected data passes all quality checks
2. Confirm downstream data products reflect corrections
3. Run reconciliation against source data
4. Verify lineage is updated to reflect correction
5. Confirm consumer access to corrected data

---

## 7. Communication

| Severity | Recipients | Response Time |
|---|---|---|
| P0 | Technical Owner, Data Owner, Data Governance, Executive, All Consumers | Immediate |
| P1 | Technical Owner, Data Owner, Business Owner, Affected Consumers | Within 4 hours |
| P2 | Technical Owner, Data Owner | Within 24 hours |

Communication includes:
- Description of incorrect data
- Periods affected
- Root cause
- Correction action taken
- Corrected data access information
- Preventive measures

---

## 8. Prevention

1. Strengthen pre-publication quality gates
2. Implement automated data validation before Gold publication
3. Add post-publication verification checks
4. Enhance monitoring for data distribution anomalies
5. Add incorrect publication failure test
6. Review and improve quality threshold adequacy

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*