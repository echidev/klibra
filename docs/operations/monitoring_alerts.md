# FINDEX — Monitoring and Alerts

**Document Type:** Monitoring and Alerts  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This document defines the monitoring and alerting strategy for FINDEX. FINDEX requires two categories of observability: Platform Observability and Data Observability. A pipeline can be technically healthy while producing bad data; both dimensions must be monitored.

---

## 2. Platform Observability

### 2.1 Infrastructure Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| CPU Utilization | CPU usage percentage | > 85% for 5 minutes |
| Memory Utilization | Memory usage percentage | > 85% for 5 minutes |
| Disk Utilization | Disk usage percentage | > 90% |
| Network I/O | Network throughput | Anomalous spikes |
| Job Duration | Pipeline job execution time | > 2x baseline |
| Task Failures | Number of failed tasks per DAG run | > 0 for critical DAGs |

### 2.2 Orchestration Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| DAG Success Rate | Percentage of successful DAG runs | < 95% |
| DAG Failure Rate | Percentage of failed DAG runs | > 5% |
| Task Retry Rate | Percentage of tasks requiring retry | > 10% |
| DAG Run Duration | Average DAG execution time | > 2x baseline |
| Scheduled Miss | Missed scheduled runs | Any occurrence |
| Sensor Failures | Failed sensor tasks | Any occurrence |

### 2.3 Service Metrics

| Service | Metric | Alert Threshold |
|---|---|---|
| Airflow | Scheduler lag | > 30 seconds |
| PostgreSQL | Connection count | > 80% of max connections |
| S3/MinIO | Request latency | > 99th percentile baseline |
| Spark | Job failure rate | > 5% |

---

## 3. Data Observability

### 3.1 Freshness

| Metric | Description | Alert Threshold |
|---|---|---|
| Publication Lag | Time between publication_date and availability | Exceeds SLA per dataset |
| Ingestion Lag | Time between publication_date and ingestion_timestamp | Exceeds freshness SLA |
| Staleness | Time since last successful ingestion | Exceeds staleness alert hours |

### 3.2 Volume Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| Row Count | Total records per dataset | ±20% from baseline |
| File Count | Number of files per partition | Anomalous change |
| Payload Size | Size of ingested payload | Anomalous change |

### 3.3 Quality Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| Null Rate | Percentage of null values in non-nullable fields | > 0% |
| Duplicate Rate | Percentage of duplicate records | > 0% for key fields |
| Quality Failure Rate | Percentage of records failing quality checks | > 0% (P0/P1) |
| Distribution Anomaly | Statistical deviation in value distributions | > 3 standard deviations |
| Schema Change | Detected schema modifications | Any breaking change |
| Missing Periods | Gaps in time series | > 1 period |

### 3.4 Temporal Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| Observation Date Gap | Missing observation periods | > 1 missing period |
| Publication Date Anomaly | Unexpected publication dates | Any anomaly |
| Revision Rate | Frequency of historical revisions | Significant increase |

---

## 4. Alerting

### 4.1 Alert Principles

All alerts must be:

- **Actionable** — Each alert must have a clear action to take
- **Deduplicated** — Duplicate alerts are consolidated
- **Severity-based** — Routing and response time based on P0–P3
- **Routed to responsible owners** — Alert goes to the correct person/team
- **Linked to relevant run metadata** — Alert includes run_id, dataset_id, and diagnostic information

### 4.2 Alert Examples

| Alert Name | Description | Severity | Action |
|---|---|---|---|
| Dataset freshness breached | Dataset not refreshed within SLA | P2 | Investigate pipeline; retry if needed |
| Schema breaking change detected | Breaking schema change in source | P0 | Halt pipeline; investigate; escalate |
| P1 quality rule failed | Critical quality check failure | P1 | Quarantine failing records; investigate |
| Source unavailable | External source unreachable | P1/P2 | Retry; activate alternate source if available |
| Pipeline exceeded runtime threshold | Job running longer than expected | P2 | Investigate; consider scaling |
| Unexpected record-count change | Record count deviates significantly | P1/P2 | Investigate source and pipeline |
| Missing periods detected | Gaps in time series | P2 | Investigate source; backfill if needed |
| Quality score below threshold | Dataset quality score drops | P1 | Investigate; quarantine if needed |
| Freshness SLA breach | Dataset not meeting freshness target | P2 | Investigate; alert Data Owner |
| Ingestion failure | Pipeline ingestion task failed | P1 | Retry; investigate root cause |

### 4.3 Alert Routing

| Severity | Routing | Response Time |
|---|---|---|
| P0 | Technical Owner, Data Governance, Executive Management, On-call | Immediate |
| P1 | Technical Owner, Data Owner, Business Owner | Within 1 hour |
| P2 | Technical Owner, Data Owner | Within 4 hours |
| P3 | Technical Owner | Within 24 hours |

---

## 5. Dashboards

### 5.1 Platform Dashboard

- Pipeline execution status (success/failure rates)
- Resource utilization (CPU, memory, disk)
- Job duration trends
- Task failure counts
- Service health status

### 5.2 Data Dashboard

- Dataset freshness (days since last refresh)
- Quality score trends per dataset
- Quality outcome distribution
- Record count trends
- Freshness SLA adherence rate
- Schema change history
- Missing period alerts

---

## 6. Monitoring Tools

| Tool | Purpose |
|---|---|
| CloudWatch | Infrastructure monitoring |
| OpenTelemetry | Distributed tracing and metrics |
| Airflow UI | Orchestration monitoring |
| PostgreSQL | Operational metadata queries |
| Data Observability Platform | Data quality and freshness monitoring |

---

## 7. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*