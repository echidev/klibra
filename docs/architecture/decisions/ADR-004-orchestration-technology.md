# ADR-004 — Orchestration Technology

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX requires an orchestration platform to schedule and manage recurring data pipelines, handle dependencies between tasks, implement retry logic, and provide operational visibility into pipeline execution. The orchestrator must support complex DAGs, idempotent execution, failure handling, and monitoring.

---

## Decision

Apache Airflow is the candidate orchestration platform for FINDEX. Airflow provides a mature, widely-adopted framework for defining, scheduling, and monitoring data pipelines as Directed Acyclic Graphs (DAGs).

---

## Alternatives Considered

### Alternative A: Apache Airflow (Selected)

| Aspect | Assessment |
|---|---|
| Pros | Mature ecosystem; DAG-based; extensive operator library; active community; supports retries, sensors, branching; good monitoring; local and managed options |
| Cons | Operational overhead for self-managed; resource-intensive; UI can be complex |
| Verdict | **Selected** — Best fit for FINDEX requirements |

### Alternative B: Prefect

| Aspect | Assessment |
|---|---|
| Pros | Modern Python-native; simpler API; good for dynamic workflows |
| Cons | Smaller community; less mature ecosystem; fewer integrations |
| Verdict | **Rejected** — Less mature than Airflow |

### Alternative C: Dagster

| Aspect | Assessment |
|---|---|
| Pros | Data-aware; software-defined assets; strong typing |
| Cons | Smaller community; newer product; less proven at enterprise scale |
| Verdict | **Rejected** — Less mature and fewer production references |

### Alternative D: Custom Scheduler

Build a custom scheduler using Python scripts and cron.

| Aspect | Assessment |
|---|---|
| Pros | Full control; minimal dependencies |
| Cons | Reinventing the wheel; no monitoring, retry, dependency management; high maintenance |
| Verdict | **Rejected** |

---

## Consequences

### Positive

1. **DAG-based orchestration** — Complex pipeline dependencies clearly modeled
2. **Mature ecosystem** — Extensive operators, sensors, and hooks for various data sources
3. **Retry and failure handling** — Built-in retry policies and failure classification
4. **Monitoring** — UI, metrics, and alerting built in
5. **Local and managed** — Can run locally via Docker and scale to managed Airflow in AWS
6. **Community** — Large community and extensive documentation

### Negative

1. **Resource usage** — Airflow scheduler and webserver require resources
2. **Complexity** — DAG authoring and configuration can be complex for large pipelines
3. **Operational overhead** — Self-managed Airflow requires maintenance (mitigated by managed Airflow in production)

---

## DAG Structure

```text
discover
  ↓
extract
  ↓
raw_validation
  ↓
bronze
  ↓
quality_gate
  ↓
silver
  ↓
silver_quality
  ↓
gold
  ↓
publish
  ↓
notify
```

Tasks should be independently observable and retryable.

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage — pipeline outputs stored in object storage |
| ADR-002 | Source ingestion interface — DAG tasks invoke connectors |
| ADR-005 | Transformation framework — dbt tasks invoked within DAG |
| Local Development | Docker Compose includes Airflow |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*