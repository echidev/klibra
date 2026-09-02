# ADR-005 — Transformation Framework

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX requires multiple transformation approaches to handle different types of data processing:

1. Source-specific parsing and extraction (procedural logic)
2. Large-scale distributed transformations (big data volumes)
3. SQL-based curated transformations with testing and documentation
4. Local analytical validation and lightweight development

No single framework optimally serves all these needs. The transformation architecture must match each workload type while maintaining consistency and reproducibility.

---

## Decision

FINDEX shall use a multi-framework transformation architecture:

- **Python** for source-specific parsing, file extraction, API clients, and complex procedural logic
- **Spark** for distributed processing when data volume warrants it
- **dbt** for SQL-based transformations, data tests, documentation, and dependency graphs
- **DuckDB** for local analytical validation and lightweight development

---

## Alternatives Considered

### Alternative A: Single Framework for All Transformations

Use one framework (e.g., Spark) for all transformation needs.

| Aspect | Assessment |
|---|---|
| Pros | Consistency; single ecosystem |
| Cons | Overkill for simple transformations; Python procedural logic difficult in Spark; dbt SQL better for curated transformations |
| Verdict | **Rejected** |

### B: Multi-Framework Approach (Selected)

Each framework used for its optimal workload.

| Aspect | Assessment |
|---|---|
| Pros | Each tool used for its strength; cost-efficient; scalable; maintainable |
| Cons | Multiple frameworks to learn and maintain; integration complexity |
| Verdict | **Selected** — Aligns with TDD Section 24 |

### Alternative C: dbt Only

Use dbt for all transformations.

| Aspect | Assessment |
|---|---|
| Pros | SQL-based; documentation; testing; dependency graphs |
| Cons | Cannot handle source-specific parsing; limited procedural logic; not suitable for distributed processing |
| Verdict | **Rejected** — Insufficient for all workload types |

---

## Consequences

### Positive

1. **Optimal tool usage** — Each framework handles its best workload
2. **Cost efficiency** — Spark used only when volume justifies it
3. **Maintainability** — Python for complex procedural logic, dbt for SQL transformations
4. **Testing** — dbt provides built-in data tests
5. **Documentation** — dbt auto-generates documentation
6. **Local development** — DuckDB enables local validation without full infrastructure
7. **Scalability** — Spark handles large-scale processing

### Negative

1. **Multiple frameworks** — Team must be proficient in Python, dbt SQL, and Spark
2. **Integration complexity** — Frameworks must interoperate correctly
3. **Operational overhead** — Multiple frameworks to monitor and maintain

---

## Framework Responsibilities

| Framework | Responsibility | When Used |
|---|---|---|
| **Python** | API clients, file extraction, source-specific parsing, complex procedural logic | Always |
| **Spark** | Distributed transformation, large historical processing | When volume warrants |
| **dbt** | SQL-based transformations, data tests, documentation, dependency graphs | Always for Silver/Gold |
| **DuckDB** | Local analytical validation, lightweight development, ad-hoc inspection | Development only |

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage — input/output for all transformations |
| ADR-002 | Source ingestion — Python handles source extraction |
| ADR-003 | Canonical model — transformations map to canonical structure |
| ADR-004 | Orchestration — Airflow invokes transformations |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*