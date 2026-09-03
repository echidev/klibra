# Runbook — Quality Failure

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §32 (quality gates), §60 (quality); TDD §21 (quality framework), §22 (severity)  

---

## 1. Purpose

Provide procedures for responding when data fails a blocking quality check (P0 or P1) during pipeline execution.

---

## 2. Detection

- Airflow task fails with `error_type = QualityFailure`.
- Quality‑gate alert triggers (P0/P1 violation).
- Monitoring dashboard shows quality score drop.

---

## 3. Diagnosis

1. Identify the **failed dataset** and **quality rule** (e.g., nullability, duplicate rate).
2. Review the **error log** for details (row examples, offending values).
3. Determine whether the failure originates from:
   - **Source data** (invalid values, missing fields).
   - **Transformation logic** (incorrect mapping, aggregation).
   - **Schema drift** (unexpected column change).
4. Check recent **source changes** (Runbook‑Source‑Outage, Change Management).
5. Verify **idempotency** and **replay** expectations.

---

## 4. Containment

1. Halt further processing of the affected dataset (pause Airflow DAG).
2. Quarantine the failing records in `quarantine/`.
3. Alert Technical Owner, Data Owner, and Business Owner.
4. Notify downstream consumers of potential data impact.

---

## 5. Resolution

### 5.1 Source Data Issue

- Coordinate with the **Source Owner** to correct the source payload.
- Re‑run ingestion for the affected period (Runbook‑Backfill).
- Update source contract if needed.

### 5.2 Transformation Bug

- Fix the transformation code (dbt model, Spark job, Python script).
- Add unit tests for the failing rule.
- Run the pipeline for the affected period in staging.
- Validate that quality checks now pass.

### 5.3 Schema Drift

- Update the **data contract** to reflect the new schema.
- Adjust transformation mappings accordingly.
- Run a **schema compatibility test** before production deployment.

---

## 6. Validation

1. Verify the **quality check** now passes (no P0/P1 violations).
2. Re‑run downstream validation (Gold layer, semantic metrics).
3. Confirm lineage records reflect the corrected run.
4. Ensure **freshness SLA** is still met.

---

## 7. Communication

- Immediate alert to Technical Owner and Data Owner.
- Status updates during investigation and remediation.
- Final communication to Business Owner and downstream consumers.

---

## 8. Prevention

- Add **regression tests** for the failed rule.
- Improve **source monitoring** to catch anomalies early.
- Review **schema change detection** alerts.
- Enhance **data contract review** process for new source fields.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Updated for KLIBRA PRD v2.0 / TDD v2.0; clarified source vs transformation origin, added regression test step |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
