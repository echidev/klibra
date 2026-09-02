# Runbook — Source Outage

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for responding when an external data source becomes unavailable, affecting the FINDEX ingestion pipeline.

---

## 2. Detection

- Pipeline alert: source unreachable, HTTP 5xx, connection timeout
- Monitoring: freshness breach for affected dataset
- Airflow task failure with network/source error type
- Multiple consecutive retry failures

---

## 3. Diagnosis

1. Verify source outage: check source website, API status page, or contact source institution
2. Check if outage is isolated to FINDEX or affects multiple consumers
3. Assess expected duration of outage
4. Review last successful ingestion timestamp and data coverage
5. Check if alternate access method exists (file download, portal)

---

## 4. Containment

1. Log the outage with start time and source details
2. Alert stakeholders based on severity
3. Pause automated retries if outage is prolonged (avoid unnecessary load)
4. Document all details in incident management system

---

## 5. Recovery

### 5.1 Short Outage (Expected < 24 hours)

1. Configure retry with exponential backoff
2. Monitor source availability
3. Resume ingestion when source is restored
4. Verify data completeness after recovery
5. Check for gaps in time series

### 5.2 Prolonged Outage (Expected > 24 hours)

1. Activate alternate approved source method if available:
   - Official portal download instead of API
   - Partner data source if available
   - Cached or archived data if applicable
2. Notify Business Owner and Data Owner
3. Assess impact on downstream data products
4. Evaluate need for backfill when source is restored
5. Consider manual data entry if critical and no alternate source

### 5.3 Permanent Discontinuation

1. Initiate source deprecation process
2. Evaluate replacement source
3. Update Source Catalog status to deprecated
4. Preserve historical data in Raw layer
5. Update downstream consumers on impact
6. Document in change log

---

## 6. Validation

1. Verify source restoration with test connection
2. Run test ingestion on staging
3. Validate data completeness and quality
4. Resume full pipeline
5. Verify freshness returns to normal
6. Check for data gaps and assess if backfill needed

---

## 7. Communication

| Severity | Recipients | Lead Time |
|---|---|---|
| P0 | Technical Owner, Data Owner, Business Owner, Executive | Immediate |
| P1 | Technical Owner, Data Owner, Business Owner | Within 4 hours |
| P2 | Technical Owner, Data Owner | Daily update |

Communication includes:
- Outage start time and expected duration
- Impact on data products
- Mitigation steps taken
- Recovery timeline

---

## 8. Prevention

1. Maintain alternate source methods for critical datasets
2. Monitor source health proactively (synthetic checks)
3. Build relationship with source institution contacts
4. Cache recent data where licensing permits
5. Implement circuit breaker pattern for repeated failures

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*