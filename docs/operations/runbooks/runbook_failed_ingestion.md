# Runbook — Failed Ingestion

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §12 (functional requirements), §15 (reliability); TDD §26 (pipeline failure handling), §33 (CI/CD), §46 (incident management)  

---

## 1. Purpose

Step-by-step procedures for responding to a failed KLIBRA ingestion pipeline. The goal is to detect, diagnose, contain, recover, validate, communicate, and prevent recurrence.

---

## 2. Detection

### 2.1 Symptoms

- Pipeline status shows `failed` in Airflow UI.
- Alert triggered (freshness breach, task failure, quality gate breach).
- Expected dataset not appearing in downstream layers.
- Monitoring dashboard shows elevated error rate.

### 2.2 Initial Triage

1. Open Airflow UI and identify the failed DAG and task.
2. Check the alert details (severity, dataset, timestamp).
3. Note the pipeline `run_id`.
4. Determine whether the failure is isolated to one dataset or affects multiple.

---

## 3. Diagnosis

### 3.1 Identify Failure Type

Per TDD §26:

| Failure Type | Indicators |
| --- | --- |
| Authentication | Auth error message, credential expired |
| Network | Timeout, connection refused |
| Source availability | Source unreachable, HTTP 5xx |
| Rate limiting | HTTP 429, throttling messages |
| Schema change | Schema mismatch, missing fields |
| Parsing | Malformed payload, parse errors |
| Data quality | Quality check failures |
| Transformation | Transformation logic errors |
| Storage | Write failures, permission errors |
| Dependency | Downstream service unavailable |
| Infrastructure | Resource exhaustion, container crashes |

### 3.2 Gather Information

- Check pipeline run metadata in PostgreSQL.
- Review logs for the failed task.
- Check content hash and payload integrity.
- Review the ingestion metadata record.
- Verify source availability (check source website / API).

---

## 4. Containment

1. **Do not rerun immediately** — understand the root cause first.
2. **Isolate the failed batch** — mark as quarantined if quality-related.
3. **Alert the relevant stakeholders** — notify Data Owner and Business Owner for P0/P1.
4. **Document the failure** — record in the incident management system.

---

## 5. Recovery

### 5.1 By Failure Type

| Failure Type | Recovery Action |
| --- | --- |
| Network timeout | Retry with exponential backoff |
| Source unavailable | Wait for source restoration; check alternate method (Runbook‑Source‑Outage) |
| Authentication failure | Rotate credentials; verify new credentials; rerun (Runbook‑Auth‑Failure) |
| Rate limiting | Back off and retry; contact source if persistent (TDD §73) |
| Schema change | Evaluate change type; adapt connector (Runbook‑Schema‑Drift) |
| Parsing error | Fix parser; validate against new payload format |
| Data quality | Quarantine failing records; investigate root cause (Runbook‑Quality‑Failure) |
| Transformation error | Fix transformation code; test in staging |
| Storage failure | Verify storage availability; fix permissions; rerun |
| Dependency failure | Wait for dependency; retry after resolution |
| Infrastructure | Scale resources; restart service; investigate root cause |

### 5.2 Rerun Procedure

1. Confirm root cause is resolved.
2. Validate source data availability.
3. Rerun with **idempotency key** to prevent duplication (TDD §15, §71).
4. Monitor rerun to completion.
5. Verify quality checks pass.

---

## 6. Validation

1. Verify record count matches expected range.
2. Verify quality status is `ACCEPTED` or `ACCEPTED_WARNING`.
3. Verify freshness is within SLA.
4. Verify downstream layers are updated.
5. Run spot-check queries on curated data.
6. Confirm no duplicate observations.
7. Verify lineage is intact.

---

## 7. Communication

### 7.1 Notification Recipients

| Severity | Recipients |
| --- | --- |
| **P0** | Technical Owner, Data Owner, Data Governance, Executive Management |
| **P1** | Technical Owner, Data Owner, Business Owner |
| **P2** | Technical Owner, Data Owner |
| **P3** | Technical Owner |

### 7.2 Communication Template

```text
Subject: [SEVERITY] Pipeline Failure — {dataset_id} — {run_id}

Pipeline: {pipeline_id}
Run ID: {run_id}
Dataset: {dataset_id}
Severity: {P0/P1/P2/P3}
Failure Type: {type}
Detected At: {timestamp}
Status: {investigating/resolved/recovered}
Root Cause: {root cause}
Impact: {impact description}
Recovery Action Taken: {action}
Expected Resolution: {timestamp}
```

---

## 8. Prevention

1. **Root cause analysis** — document why the failure occurred.
2. **Preventive action** — implement fix to prevent recurrence.
3. **Monitor effectiveness** — watch for recurrence.
4. **Update runbook** — refine procedures based on lessons learned.
5. **Add monitoring** — add new alerts if gap identified.
6. **Test resilience** — add failure test if applicable (TDD §44).

---

## 9. Documentation Requirements

After resolution, document:

| Field | Description |
| --- | --- |
| Incident ID | Unique identifier |
| Start time | When failure was detected |
| Detection time | When alert triggered |
| Affected dataset | Dataset(s) affected |
| Severity | P0–P3 |
| Impact | What was affected |
| Root cause | Why it failed |
| Resolution | How it was fixed |
| Recovery actions | Steps taken to recover |
| Preventive actions | Steps to prevent recurrence |
| Owner | Who managed the incident |

---

## 10. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re-aligned to KLIBRA PRD v2.0 / TDD v2.0; expanded recovery matrix, added cross-references to related runbooks, refined communication template |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
