# Runbook — Duplicate Data

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §42 (idempotency), §60 (quality); TDD §15 (idempotency), §23 (quality)  

---

## 1. Purpose

Procedures for detecting, investigating, resolving, and preventing duplicate data in KLIBRA.

---

## 2. Detection

- Duplicate‑rate quality check exceeds 0 % for primary‑key fields.
- Unexpected row‑count increase (>20 % deviation from baseline).
- Downstream consumer reports inconsistent metric values.
- Airflow task rerun without idempotency check.

---

## 3. Diagnosis

### 3.1 Identify Duplicate Type

| Duplicate Type | Indicators |
| --- | --- |
| Ingestion duplicate | Same source payload ingested twice (`run_id` differs). |
| Pipeline rerun duplicate | Same run produced multiple copies of the same record. |
| Transformation duplicate | Join or aggregation logic created unintended row multiplication. |
| Source duplicate | Source API returned duplicate records in a single response. |

### 3.2 Root‑Cause Investigation

1. Inspect `run_id` and `payload_hash` in the duplicate records.
2. Review Airflow DAG run history for retries or late retries.
3. Check the idempotency‑key definition (ADR‑007, TDD §71).
4. Review transformation code for cross‑join or un‑grouped aggregation.
5. Verify the connector handles pagination correctly.

---

## 4. Containment

1. Halt further ingestion for affected dataset.
2. Quarantine duplicate records in the `quarantine/` layer.
3. Alert **Technical Owner** and **Data Owner**.
4. Communicate to downstream consumers that data may be affected.

---

## 5. Resolution

### 5.1 Ingestion Duplicate

1. Identify the duplicate batch via `run_id` and `payload_hash`.
2. Delete the duplicate batch from Bronze, Silver, and Gold.
3. Re‑run ingestion with corrected idempotency key.
4. Verify duplicate rate returns to 0 %.

### 5.2 Transformation Duplicate

1. Identify the duplicate via primary‑key comparison.
2. Fix the transformation logic (e.g., correct join condition).
3. Re‑run the transformation from Bronze through Silver and Gold.
4. Verify duplicate rate returns to 0 %.

### 5.3 Source Duplicate

1. Document the source duplication pattern.
2. Add deduplication logic in the connector using `payload_hash`.
3. Remove the duplicate from downstream layers.
4. Add monitoring to detect recurrence.

---

## 6. Validation

1. Verify duplicate rate is 0 % for primary‑key fields.
2. Verify row count matches expected baseline.
3. Run all quality checks (P0/P1 must pass).
4. Confirm downstream data products are consistent.
5. Verify lineage is intact (Runbook‑Data‑Restoration if data loss occurs).

---

## 7. Communication

- Alert Technical Owner and Data Owner immediately.
- Notify Business Owner if published data was affected.
- Provide status updates during resolution.
- Confirm resolution in the incident ticket.

---

## 8. Prevention

1. Ensure idempotency keys are properly implemented and tested.
2. Add duplicate‑rate monitoring and alerting.
3. Review transformation logic for unintended row multiplication before deployment.
4. Test idempotency in staging before production deployment.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; added duplicate type table, root‑cause analysis, resolution steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
