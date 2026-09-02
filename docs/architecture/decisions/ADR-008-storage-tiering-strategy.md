# ADR-008 — Storage Tiering Strategy

**Status:** Proposed  
**Date:** 2026-09-02  
**Author:** FINDEX Data Platform Engineering  
**Deciders:** FINDEX Architecture Team  
**Supersedes:** None  

---

## Context

FINDEX stores large volumes of data across multiple layers (Raw, Bronze, Silver, Gold) with varying access patterns. Raw data is accessed infrequently but must be preserved long-term. Gold data is accessed frequently for analytical queries. Storage costs must be controlled as data volumes grow.

---

## Decision

FINDEX shall implement a storage tiering strategy with four tiers: Hot, Warm, Cold, and Archive. Data automatically transitions between tiers based on age and access patterns.

---

## Alternatives Considered

### Alternative A: Single Storage Tier

All data stored in the same storage class.

| Aspect | Assessment |
|---|---|
| Pros | Simple; no tiering management |
| Cons | High cost for cold/historical data; no cost optimization |
| Verdict | **Rejected** |

### B: Multi-Tier Storage (Selected)

Four tiers with automatic transition policies.

| Aspect | Assessment |
|---|---|
| Pros | Cost-optimized; automated lifecycle management; appropriate for varying access patterns |
| Cons | Requires configuration; transition latency for archive access |
| Verdict | **Selected** |

### Alternative C: Manual Tiering

Manually move data between storage classes.

| Aspect | Assessment |
|---|---|
| Pros | Full control |
| Cons | High operational overhead; error-prone; not scalable |
| Verdict | **Rejected** |

---

## Consequences

### Positive

1. **Cost efficiency** — Historical data stored in cheaper tiers automatically
2. **Automation** — Lifecycle policies reduce manual intervention
3. **Scalability** — Cost grows linearly with data, not exponentially
4. **Compliance** — Retention policies enforced automatically

### Negative

1. **Transition latency** — Retrieval from archive tiers has latency
2. **Configuration complexity** — Lifecycle policies must be carefully defined
3. **Monitoring** — Tier transitions must be monitored

---

## Tier Definitions

| Tier | Storage Class | Transition | Retention |
|---|---|---|---|
| **Hot** | Standard | Immediate | 0–90 days |
| **Warm** | Infrequent Access | After 90 days | 90 days–2 years |
| **Cold** | Glacier/Archive | After 2 years | 2–10 years |
| **Archive** | Deep Archive | After 10 years | Per retention policy |

---

## Related Decisions

| ADR | Relationship |
|---|---|
| ADR-001 | Object storage — base storage layer |
| ADR-007 | Temporal model — age determines tiering |

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Platform Engineering | Initial draft |

---

*This ADR is classified as Internal.*