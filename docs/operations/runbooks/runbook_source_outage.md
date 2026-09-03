# Runbook — Source Outage

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §10 (scope), §11 (source registration); TDD §13 (connector), §48 (source change management), §60 (source catalog)  

---

## 1. Purpose

Provide procedures for responding when an external data source becomes unavailable, affecting the KLIBRA ingestion pipeline.

---

## 2. Detection

- Pipeline alert: source unreachable, HTTP 5xx, connection timeout.
- Monitoring: freshness breach for affected dataset.
- Airflow task failure with `error_type = SourceUnavailable`.
- Multiple consecutive retry failures.

---

## 3. Diagnosis

1. Verify the outage: check the source website, API status page, or contact the source institution.
2. Determine whether the outage is **isolated to KLIBRA** or affects multiple consumers.
3. Assess the expected duration of the outage.
4. Review the **last successful ingestion** timestamp and data coverage.
5. Check whether an **alternate access method** exists (file download, portal).

---

## 4. Containment

1. Log the outage with start time and source details.
2. Alert stakeholders based on severity.
3. Pause automated retries if outage is prolonged (avoid unnecessary load).
4. Document all details in the incident management system.

---

## 5. Recovery

### 5.1 Short Outage (Expected < 24 h)

1. Configure retry with exponential backoff.
2. Monitor source availability.
3. Resume ingestion when source is restored.
4. Verify data completeness after recovery.
5. Check for gaps in time series.

### 5.2 Prolonged Outage (Expected > 24 h)

1. Activate alternate approved source method if available:
   - Official portal download instead of API.
   - Alternate API endpoint if documented.
   - Cached or archived data if licensing permits.
2. Notify Business Owner and Data Owner.
3. Assess impact on downstream data products.
4. Evaluate need for backfill when source is restored.
5. Consider manual data entry only if critical and no alternate source.

### 5.3 Permanent Discontinuation

1. Initiate **source deprecation** process (Change Management).
2. Evaluate replacement source.
3. Update the **Source Catalog** status to deprecated.
4. Preserve historical data in the Raw layer.
5. Update downstream consumers on impact.
6. Document in the change log.

---

## 6. Validation

1. Verify source restoration with a test connection.
2. Run a test ingestion in staging.
3. Validate data completeness and quality.
4. Resume full pipeline.
5. Verify freshness returns to normal.
6. Check for data gaps and trigger a backfill if needed (Runbook‑Backfill).

---

## 7. Communication

| Severity | Recipients | Lead Time |
| --- | --- | --- |
| **P0** | Technical Owner, Data Owner, Business Owner, Executive | Immediate |
| **P1** | Technical Owner, Data Owner, Business Owner | Within 4 h |
| **P2** | Technical Owner, Data Owner | Daily update |

Communication includes: outage start time, expected duration, impact on data products, mitigation steps, and recovery timeline.

---

## 8. Prevention

1. Maintain alternate source methods for critical datasets.
2. Monitor source health proactively (synthetic API checks).
3. Build relationships with source institution contacts.
4. Cache recent data where licensing permits (raw‑layer immutable archive).
5. Implement circuit‑breaker pattern for repeated failures (TDD §73).

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; added resolution paths, communication matrix, prevention steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
