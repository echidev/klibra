# Runbook — Schema Drift

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §19 (schema drift), §29 (data contracts); TDD §19 (schema evolution), §23 (quality)  

---

## 1. Purpose

Provide procedures for handling schema drift—unexpected changes in source schema that may break pipelines or data contracts.

---

## 2. Detection

- Schema‑drift detection alert (e.g., new column, type change).
- Airflow task failure with `error_type = SchemaDrift`.
- Quality‑gate failure due to unexpected field.
- Manual audit discovers mismatched schema between source and contract.

---

## 3. Diagnosis

1. Identify the **source** and **dataset** exhibiting drift.
2. Compare the **current source schema** (via connector metadata) to the **recorded schema** in the data contract.
3. Classify the change:
   - **Compatible** (e.g., new nullable field, metadata‑only change).
   - **Potentially Breaking** (e.g., type widening, new required field).
   - **Breaking** (e.g., removed field, type narrowing, changed enumeration).
4. Determine impact on:
   - Bronze ingestion.
   - Silver standardization.
   - Gold business logic.
5. Check recent **source change management** entries.

---

## 4. Containment

1. Pause the affected Airflow DAG.
2. Quarantine any partially processed data.
3. Alert Technical Owner, Data Owner, and Data Governance.
4. Notify downstream consumers of possible data quality impact.

---

## 5. Resolution

### 5.1 Compatible Change

- Update the **source catalog** to reflect new optional fields.
- No pipeline code change required.
- Run a **schema validation test** to ensure compatibility.

### 5.2 Potentially Breaking Change

1. Update the **data contract** to include the new field definition (nullable if appropriate).
2. Adjust transformation code to handle the new field (e.g., default values, type casting).
3. Run unit and integration tests in staging.
4. Deploy the updated contract and code via CI/CD.
5. Re‑process affected periods if needed.

### 5.3 Breaking Change

1. **Engage the Source Owner** to understand the change rationale.
2. If possible, request a **fallback** to the previous schema or provide a migration path.
3. Update the **data contract** with the new required fields and deprecate old ones.
4. Implement **migration logic** (e.g., map old field to new, default values).
5. Conduct a full **backfill** for the affected periods (Runbook‑Backfill).
6. Validate quality checks and lineage.

---

## 6. Validation

1. Verify **schema validation** passes for Bronze and Silver layers.
2. Run all **quality checks** (P0/P1) – must pass.
3. Confirm **lineage** captures the schema version used.
4. Ensure downstream Gold products are unchanged (or updated if intentional).

---

## 7. Communication

- Immediate alert to Technical Owner, Data Owner, Data Governance.
- Status updates during investigation and remediation.
- Final communication to Business Owner and downstream consumers.

---

## 8. Prevention

- Enable **schema‑drift monitoring** (run daily schema comparison).
- Require **contract update** for any source schema change (Change Management Process).
- Add **unit tests** for schema compatibility.
- Conduct **impact analysis** before accepting source changes.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Updated for KLIBRA PRD v2.0 / TDD v2.0; added classification of changes, backfill steps, and prevention measures |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
