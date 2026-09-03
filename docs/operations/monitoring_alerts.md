# KLIBRA — Monitoring and Alerts

**Document Type:** Monitoring and Alerts  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §59 (observability), §60 (cost), §71 (ops); TDD §29 (observability), §30 (monitoring), §31 (security), §44 (cost management)  

---

## 1. Purpose

Define the monitoring and alerting strategy for KLIBRA, covering both **Platform Observability** and **Data Observability**. Ensures that technical health and data quality are continuously monitored and actionable alerts are routed to responsible owners (PRD §59‑§61, TDD §29‑§31).

---

## 2. Monitoring Categories

### 2.1 Platform Observability

| Metric | Description | Alert Threshold |
| --- | --- | --- |
| CPU Utilization | CPU usage percentage per compute instance | > 85 % for 5 min |
| Memory Utilization | Memory usage percentage | > 85 % for 5 min |
| Disk Utilization | Disk usage percentage | > 90 % |
| Network I/O | Throughput, latency | Anomalous spikes |
| Job Duration | Pipeline job execution time | > 2× baseline |
| Task Failures | Number of failed tasks per DAG run | > 0 for critical DAGs |
| Scheduler Lag | Airflow scheduler lag | > 30 s |
| DB Connections | PostgreSQL connection count | > 80 % of max connections |
| S3 Request Latency | Object store request latency | > 99th percentile baseline |
| Spark Job Failure Rate | Spark job failures per batch | > 5 % |

### 2.2 Data Observability

| Metric | Description | Alert Threshold |
| --- | --- | --- |
| Freshness (Lag) | Time between `publication_date` and latest ingestion | Exceeds SLA per dataset (PRD §60.1) |
| Row Count Deviation | ±20 % from expected row count | Deviation > 20 % |
| Null Rate | Percentage of nulls in non‑nullable fields | > 0 % |
| Duplicate Rate | Duplicate primary‑key rows | > 0 % |
| Quality Failure Rate | P0/P1 violations per dataset | Any P0/P1 violation |
| Distribution Anomaly | Statistical deviation in value distribution | > 3 σ from baseline |
| Schema Change Detection | Detected schema modifications | Any breaking change |
| Missing Periods | Gaps in expected observation periods | Any missing period |
| Confidence / Coverage | Intelligence product coverage below threshold | Below configured coverage |

---

## 3. Alerting Principles

All alerts must be:

- **Actionable** – Include clear remediation steps.
- **Deduplicated** – Consolidated to avoid noise.
- **Severity‑Based** – Routed based on P0‑P3 classification.
- **Routed to responsible owners** – Refer to `access_review_process.md` for owners.
- **Linked to run metadata** – Include `run_id`, `dataset_id`, and diagnostic info.

---

## 4. Alert Examples

| Alert Name | Description | Severity | Action |
|---|---|---|
| Dataset freshness breached | Dataset not refreshed within SLA | P2 | Investigate pipeline; retry if needed |
| Schema breaking change detected | Breaking schema change in source | P0 | Halt pipeline; investigate source; update contract |
| P1 quality rule failed | Critical quality check failure | P1 | Quarantine failing records; investigate source and transformation |
| Source unavailable | External source unreachable | P1 / P2 | Retry; activate alternate source if available |
| Pipeline exceeded runtime threshold | Job running longer than expected | P2 | Investigate resource allocation; scale if needed |
| Unexpected record‑count change | Row count deviates significantly | P1 | Verify source payload; check for schema drift |
| Missing periods detected | Gaps in time series | P2 | Backfill missing periods |
| Quality score below threshold | Dataset quality score dips below configured level | P1 | Review data quality rules; trigger investigation |

---

## 5. Alert Routing Matrix

| Severity | Routing |
| --- | --- |
| **P0** | Technical Owner, Data Governance, Executive Management (immediate) |
| **P1** | Technical Owner, Data Owner, Business Owner (within 1 h) |
| **P2** | Technical Owner, Data Owner (within 4 h) |
| **P3** | Technical Owner (within 24 h) |

---

## 6. Dashboards

### 6.1 Platform Dashboard (CloudWatch)

- Pipeline execution status (success/failure rates).
- Resource utilization (CPU, memory, disk).
- Job duration trends.
- Task failure counts.
- Service health status.

### 6.2 Data Dashboard (OpenMetadata)

- Dataset freshness heatmap.
- Quality score trends per dataset.
- Outcome distribution (P0‑P3) per run.
- Record count trends.
- Freshness SLA adherence rate.
- Schema change history.
- Missing period alerts.
- Coverage and confidence for intelligence products.

---

## 7. Monitoring Tools

| Layer | Tool |
| --- | --- |
| Infrastructure Metrics | CloudWatch, CloudWatch Logs |
| Distributed Tracing | OpenTelemetry (via AWS X‑Ray) |
| Data Quality & Lineage | OpenMetadata |
| Airflow UI | DAG run status, task logs |
| Query Engine | Athena query metrics |
| Alerting | CloudWatch Alarms → SNS → PagerDuty (or Slack) |

---

## 8. Cost Management Integration

- **Query monitoring** tracks Athena cost per dataset.
- **Object lifecycle** cost impact visualized on storage dashboards.
- **Budget alerts** trigger when monthly spend exceeds threshold.
- **Partition optimization** metrics feed back into cost‑reduction recommendations.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; added data observability metrics, alert examples, routing matrix, and cost integration |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
