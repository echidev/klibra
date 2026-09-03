# Runbook — Incorrect Publication

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §12 (publication), §15 (reconciliation); TDD §12 (lineage), §23 (quality)  

---

## 1. Purpose

Provide procedures for handling cases where a KLIBRA data product is published with incorrect values or metadata.

---

## 2. Detection

- Quality‑gate failure flagged after publication (P0/P1).
- Downstream consumer reports unexpected values.
- Manual audit discovers mismatched totals.
- Alert from monitoring (e.g., metric deviation beyond threshold).

---

## 3. Diagnosis

1. Identify the affected **Gold product** and **time period**.
2. Compare published data against **Bronze/Silver** lineage to locate divergence.
3. Check **source data** for upstream issues (e.g., source revision).
4. Review **transformation logic** for bugs (dbt model, Spark job).
5. Verify **data contracts** and **quality rules** for the product.

---

## 4. Containment

1. Halt further publication of the affected product (pause Airflow DAG).
2. Quarantine the published dataset (move to `quarantine/`).
3. Alert Technical Owner, Data Owner, and Business Owner.
4. Notify downstream consumers of potential data impact.

---

## 5. Resolution

### 5.1 Source Issue

- If the source data was incorrect, trigger a **backfill** for the affected period (Runbook‑Backfill).
- Update source catalog with notes on source correction.

### 5.2 Transformation Bug

- Fix the transformation code (dbt model or Spark job).
- Run unit and integration tests.
- Re‑process the affected period from Bronze through Gold.
- Validate quality checks.

### 5.3 Contract Violation

- Update the data contract to reflect correct expectations.
- Re‑run contract validation.

### 5.4 Publish Corrected Data

1. Publish the corrected Gold product.
2. Record the correction run in metadata with a new `run_id`.
3. Notify downstream consumers of the corrected release.

---

## 6. Validation

1. Verify **quality checks** (P0/P1) now pass.
2. Confirm **lineage** matches the corrected source version.
3. Reconcile totals against source aggregates.
4. Ensure **freshness** SLA is met.
5. Run regression tests on downstream consumers.

---

## 7. Communication

- Immediate alert to Technical Owner, Data Owner, Business Owner.
- Status updates during investigation and remediation.
- Final communication with consumers indicating corrected data release date and impact.

---

## 8. Prevention

- Add **regression tests** for critical metrics.
- Implement **pre‑publish validation** (dry run) to catch anomalies.
- Review **data contracts** after any source change.
- Enhance **source monitoring** for data quality anomalies.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Updated for KLIBRA PRD v2.0 / TDD v2.0; refined detection, diagnosis, and resolution steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
