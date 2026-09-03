# KLIBRA — Change Management Process

**Document Type:** Change Management Process  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §23 (product governance), §29 (data contracts), §41 (decision framework); TDD §19 (schema evolution), §20 (data contracts), §48 (source change management), §81 (ADRs)  

---

## 1. Purpose

This document defines the controlled process for proposing, reviewing, approving, and implementing changes to critical definitions, schemas, quality thresholds, data contracts, semantic metrics, intelligence methodologies, and source connectors across the KLIBRA platform.

---

## 2. Scope

This process applies to changes affecting:

- **Gold data products** (`gold_macro_indicators`, `gold_interest_rate_monitor`, `gold_market_overview`, `gold_country_benchmark`, `gold_source_health`).
- **Semantic metrics** — every metric defined in the semantic metric registry (PRD §11.2, TDD §63).
- **Intelligence products** — `intelligence_economic_momentum`, `intelligence_inflation_pressure`, `intelligence_market_stress`, `intelligence_country_risk`, `intelligence_global_liquidity` (PRD §11.3).
- **Data contracts** — sources, bronze, silver, gold, semantic, intelligence (PRD §29, TDD §66).
- **Data quality rules** — thresholds, severity mapping, quarantine logic.
- **Source catalog** — new sources, deprecation, access class changes.
- **Pipeline DAGs** — orchestration structure, task logic, dependencies.
- **Lineage model** — dataset, column-level lineage capture.
- **Infrastructure** — Terraform changes affecting storage, compute, IAM, networking.
- **Metadata schema** — dataset registry, run state schema.

---

## 3. Change Classification

### 3.1 Critical (Require Full Review)

- **Breaking schema change** — removed field, type narrowing, semantic redefinition (TDD §19).
- **Semantic metric formula change** — any change to formula, grain, or dimensions (PRD §27.3).
- **Intelligence methodology change** — weighting, normalization, component set, coverage threshold (PRD §28).
- **Data contract breaking change** — schema, primary key, validity semantics.
- **Production infrastructure change** — Terraform affecting prod resources.
- **Security or access control change** — IAM policies, secrets, encryption.

### 3.2 Major (Require Standard Review)

- **Potentially breaking schema change** — type widening, new required field, changed enumerations (TDD §19).
- **Gold product addition** — new product added to the catalog.
- **New semantic metric** — addition (not modification) of a metric.
- **New intelligence product** — addition (not modification) of an intelligence score.
- **Quality threshold change** — modification of dataset-level thresholds.
- **Pipeline DAG structural change** — task ordering, branching, dependencies.

### 3.3 Minor (Routine Engineering)

- **Compatible schema change** — new nullable field, metadata-only change (TDD §19).
- **Patch-level semantic metric change** — documentation, non-semantic implementation fix (PRD §27.3).
- **Bug fix in transformation logic** without semantic change.
- **Documentation update** without contractual impact.

---

## 4. Change Request Workflow

```text
Change Identified
   ↓
Change Request Submitted (CR ticket with classification)
   ↓
Technical Impact Analysis
   ↓
Data Governance Review
   ↓
Data Owner + Business Owner Review
   ↓
Approval (Critical changes: full committee; Major: governance lead; Minor: PR review)
   ↓
Implementation (CI/CD pipeline)
   ↓
Validation (tests, staging deployment, contract validation)
   ↓
Deployment to Production
   ↓
Post-Deployment Verification
   ↓
Closure + Documentation
```

---

## 5. Change Request Format

Every change request must contain:

| Field | Description |
| --- | --- |
| **CR ID** | Unique identifier (e.g., `CR-2026-0142`) |
| **Title** | Short summary |
| **Classification** | Critical / Major / Minor |
| **Requester** | Individual or team proposing the change |
| **Affected Components** | Datasets, metrics, products, pipelines, infrastructure |
| **Description** | What is changing and why |
| **Impact Analysis** | Downstream effects on consumers, contracts, quality |
| **Rollback Plan** | How to reverse if needed |
| **Validation Strategy** | Tests, staging checks, contract validation |
| **Approval Chain** | Required reviewers and approvers |
| **Target Release** | Release version when merged |

---

## 6. Review and Approval

| Change Class | Reviewers | Approver | SLA |
| --- | --- | --- | --- |
| **Critical** | Data Owner, Technical Owner, Data Governance, Security | Data Governance Committee | 5 business days |
| **Major** | Data Owner, Technical Owner | Data Governance Lead | 3 business days |
| **Minor** | Code reviewers (PR approval) | Technical Owner | 1 business day |

Material architectural changes must additionally produce an **Architecture Decision Record (ADR)** per TDD §81.

---

## 7. Semantic Metric Change Discipline

Changes to a metric formula, grain, dimensions, or business meaning are **semantic breaking changes** (PRD §27.3) and require:

1. Major version bump (semver, TDD §61.3).
2. Explicit deprecation notice on prior major version with sunset date.
3. Updated metric registry entry (`effective_from`, `deprecation_status`, `lineage_ref`).
4. Updated semantic metric contract.
5. Communication to all known consumers.
6. Concurrent publication of both versions during deprecation window (where feasible).

A metric must not be silently redefined while retaining the same major version.

---

## 8. Intelligence Product Change Discipline

Changes to intelligence methodology (weighting, normalization, component set, coverage threshold, score band boundaries) require:

1. Methodology version bump (semver).
2. Updated intelligence methodology specification.
3. Updated `fact_intelligence_score` and `fact_intelligence_component` lineage records (TDD §65).
4. Side-by-side publication of new and old methodology for at least one observation cycle.
5. Explanation of methodology change and consumer-visible note.

---

## 9. Source Change Management

Sources must be monitored continuously for changes (TDD §48):

- URL changes.
- API changes.
- Authentication changes.
- Schema changes.
- Definition changes.
- Frequency changes.
- Historical revisions.

When the Source Catalog verifier detects a breaking source change:

1. Affected connector flagged automatically.
2. Pipeline halted for affected dataset (TDD §74).
3. Investigation by Technical Owner.
4. Contract update or connector fix.
5. Validation through contract tests.
6. Resumption only after approval.

---

## 10. Implementation Standards

- All changes via pull request; CI/CD pipeline executes validation gates (TDD §33, §79).
- Lint, unit tests, contract tests, dbt tests, semantic metric tests must pass.
- Terraform `validate` required for infrastructure changes.
- Material schema, contract, or semantic changes require staging validation and Data Owner approval before production deployment.
- Rollback tested and documented.

---

## 11. Post-Deployment

- Verification against validation strategy.
- Quality checks run on real data post-deployment.
- Incident opened if validation fails.
- Change closure documented; ADR or contract updated if material.
- Post-incident review for P0 / P1 changes.

---

## 12. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — FINDEX baseline |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Re-aligned to KLIBRA PRD v2.0 / TDD v2.0; added semantic metric change discipline (PRD §27.3), intelligence product change discipline (PRD §28), and source change monitoring (TDD §48) |

---

## 13. Document Status

This Change Management Process is an **active** governance artifact. Mandatory companion to data contracts and source catalog.

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
