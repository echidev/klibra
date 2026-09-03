# Runbook — Backfill

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §14 (historical reconstruction), §15 (backfill); TDD §17 (backfill strategy), §48 (source change management)  

---

## 1. Purpose

Provide procedures for executing **backfills** — explicit, controlled re‑ingestion of historical data for a specified period. Backfills must be explicit operations that never silently overwrite production history (PRD §15, TDD §17).

---

## 2. Triggers

- New source becomes available with historical data.
- Source publishes historical corrections or revisions.
- Connector or transformation fix requires re‑processing.
- Data quality issue requires historical correction.
- Source system migration or data format change.

---

## 3. Pre‑Fill Requirements

Before initiating a backfill, the following must be specified:

| Requirement | Description |
| --- | --- |
| **Dataset** | Which dataset is being backfilled. |
| **Start Period** | Earliest period to backfill (e.g., `2020-01-01`). |
| **End Period** | Latest period to backfill. |
| **Reason** | Why the backfill is needed. |
| **Requested By** | Who requested the backfill. |
| **Code Version** | Version of connector / transformation to use. |
| **Expected Impact** | Estimated record count and affected downstream products. |
| **Validation Strategy** | How the backfill will be validated. |
| **Approval** | Data Owner and Data Governance sign‑off. |

---

## 4. Procedure

### 4.1 Preparation

1. Obtain approval from **Data Owner** and **Data Governance**.
2. Document the backfill specification in a ticket (e.g., JIRA).
3. Freeze the production pipeline for the affected dataset (pause new runs).
4. Prepare a **staging** environment with a copy of the current production data.
5. Verify the backfill code version matches the specification.

### 4.2 Execution

1. Run the backfill in **staging** first.
2. Validate staging results:
   - Record count within expected range.
   - All quality checks pass.
   - No duplicate observations (`effective_from / effective_to`).
   - Lineage records created correctly.
3. Once validation passes, schedule the backfill for **production** via the CI/CD pipeline.
4. Deploy the backfill DAG (Airflow) with the specified `run_id` and parameters.
5. Monitor execution; ensure no unexpected failures.

### 4.3 Post‑Fill Validation

1. Verify **duplicate rate** is 0 % for key fields.
2. Verify **freshness** and **temporal semantics** are correct.
3. Run **quality checks** (P0/P1) – must pass.
4. Reconcile **source totals** vs. **Bronze/Silver/Gold** totals.
5. Ensure **lineage** captures the backfill `run_id` and version.
6. Publish updated Gold products.
7. Notify downstream consumers of the backfill.

---

## 5. Critical Rules

1. **Never silently overwrite production history.** Use `effective_from`/`effective_to` to version records (ADR‑007).
2. **Backfill must be documented** (spec, approval, execution metadata).
3. **Backfill requires approval** from Data Owner and Data Governance (Change Management Process).
4. **Backfill must be validated** in staging before production.
5. **Backfill is observable** – all runs recorded in metadata.

---

## 6. Rollback

If the backfill produces incorrect results:

1. Halt the backfill immediately.
2. Identify the cause.
3. Restore previous production state from raw immutable data (no data loss).
4. Re‑run with corrected code or parameters.
5. Validate before re‑deployment.
6. Document the rollback and root cause.

---

## 7. Communication

- Notify **Technical Owner** and **Data Owner** before backfill begins.
- Provide expected timeline and impact.
- Send **completion notification** with results and any issues.
- Update the **Source Catalog** if new source versions are introduced.

---

## 8. Documentation Updates

- Record backfill metadata in `metadata/` (manifest with `run_id`, `start_period`, `end_period`).
- Update data contracts if schema or quality thresholds change.
- Add backfill note to the dataset’s **Data Ownership Registry** entry.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Updated for KLIBRA PRD v2.0 / TDD v2.0; clarified approval, staging validation, effective‑from/to handling, and communication steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
