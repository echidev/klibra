# KLIBRA — Data Governance Policy

**Document Type:** Data Governance Policy  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §16, §17, §30‑§33; TDD §31, §57, §59, §61, §65, §71  

---

## 1. Purpose

The Data Governance Policy establishes the framework for ownership, stewardship, quality, lineage, and lifecycle management of all data assets within KLIBRA. It ensures that data is trustworthy, well‑documented, and governed according to business needs and regulatory constraints (PRD §30‑§33, TDD §59‑§62).

---

## 2. Scope

Applies to all data layers (Raw, Bronze, Silver, Gold, Quarantine, Metadata), semantic metrics, intelligence products, operational metadata, and associated contracts.

---

## 3. Data Ownership Model (Three‑Owner Model)

| Ownership Role | Responsibilities |
| --- | --- |
| **Business Owner** | Defines business definitions, KPIs, and acceptance criteria for data products; signs off on release of Gold products and semantic metrics (PRD §30). |
| **Technical Owner** | Implements pipelines, ensures technical quality, maintains contracts, monitors data health, and leads incident response (TDD §31, §57). |
| **Data Owner** | Custodian of the raw source; ensures source compliance, updates source catalog, manages source-level access (PRD §12, §13). |

All three owners must sign off on any **Critical** change (see Change Management Process).

---

## 4. Data Stewardship

Data Stewards are assigned per domain (e.g., macro‑economics, market data, credit indicators). Responsibilities:

- Maintain **data dictionary** entries (`docs/data/data_dictionary.md`).
- Review and approve **data contracts** for new datasets and changes.
- Monitor **quality metrics** (P0/P1) and trigger remediation.
- Ensure **lineage documentation** is up‑to‑date (`lineage_policy.md`).
- Coordinate with **Source Owners** for source updates.

---

## 5. Data Quality Framework

KLIBRA classifies quality severity (TDD §22) and enforces thresholds (PRD §32.3):

- **P0 (Critical)** – Must not be published; pipeline blocks.
- **P1 (High)** – Must be flagged; may be published with warning.
- **P2 (Medium)** – Acceptable but monitored.
- **P3 (Low)** – Informational.

All datasets must define **quality thresholds** in their data contracts (PRD §29) and implement **validation rules** at Bronze (raw checks), Silver (standardization checks), and Gold (business rule checks).

---

## 6. Data Lineage Policy

Lineage must be captured at **dataset level** for all datasets and **field level** where practical (TDD §28, ADR‑008). Lineage includes:

- Source identifier, dataset ID, version, and retrieval timestamps.
- Transformation step (Bronze, Silver, Gold) and responsible code version.
- Effective‑from / effective‑to timestamps for versioned records (ADR‑007).
- Connection to semantic metric definitions and intelligence methodology.

Lineage records stored in **metadata layer** (`/metadata/`) and exposed via OpenMetadata (PRD §30). Updates to lineage must be audited.

---

## 7. Data Retention & Archival

Retention policy aligns with PRD §50 and TDD §50:

| Layer | Minimum Retention | Maximum Retention |
| --- | --- | --- |
| Raw | 10 years (immutable) | 30 years (per regulatory need) |
| Bronze | 5 years | 10 years |
| Silver | 3 years | 7 years |
| Gold | 2 years | 5 years |
| Quarantine | 90 days | 180 days |
| Metadata | 5 years | 10 years |

Retention is enforced via **S3 lifecycle policies** (ADR‑008) and RDS backup retention.

---

## 8. Security & Privacy

- **Encryption in transit** (TLS 1.2+) for all data movement.
- **Encryption at rest** for Internal and Confidential data (SSE‑KMS).
- **Least‑privilege IAM** (access_review_process.md).
- **Secrets management** via AWS Secrets Manager (PRD §33, TDD §32).
- **Audit logging** for all read/write actions on Confidential data (CloudTrail, CloudWatch).
- **No PII** ingested; policy explicitly forbids collecting personal data (PRD §5, §71).

---

## 9. Governance Processes

- **Access Review Process** (see `access_review_process.md`).
- **Change Management Process** (see `change_management_process.md`).
- **Data Quality Review** – weekly quality dashboard review (Monitoring & Alerts).
- **Lineage Review** – quarterly audit of lineage completeness.
- **Retention Review** – annual check against legal requirements.
- **Incident Management** – see `incident_management.md`.

---

## 10. Roles & Responsibilities Matrix

| Role | Data Ownership | Data Stewardship | Quality Monitoring | Lineage Management | Incident Response |
| --- | --- | --- | --- | --- | --- |
| Platform Admin | Yes (infrastructure) | No | No | No | Lead |
| Data Engineer | Yes (pipeline) | Yes (technical) | Yes | Yes | Participate |
| Data Analyst | Yes (business) | Yes (semantic) | Yes (consumption) | No | Participate |
| Data Scientist | Yes (feature) | Yes (semantic) | Yes | No | Participate |
| Business Consumer | Yes (product) | No | Yes (usage) | No | No |
| Data Governance | Yes (policy) | Yes (oversight) | Yes (framework) | Yes (policy) | Yes (oversight) |

---

## 11. Documentation Requirements

All data assets must have:

- **Data contract** (source, schema, quality thresholds, retention).
- **Data dictionary entry** (description, grain, dimensions, lineage).
- **Metric definition** (for semantic metrics) – includes formula, version, owner.
- **Intelligence methodology doc** (for intelligence products).
- **Lineage map** – stored in OpenMetadata.
- **Retention schedule** – documented in contract.

Documentation lives in the `docs/` directory, version‑controlled, and reviewed per change management.

---

## 12. Review & Approval

The Data Governance Policy is reviewed annually by the **Data Governance Committee** (Platform Admin, Data Governance Lead, Business Owner). Any material amendment follows the Change Management Process and requires a **major** change classification.

---

## 13. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — FINDEX baseline |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Updated to reflect KLIBRA PRD v2.0 / TDD v2.0; added three‑owner model, clarified public‑data‑only scope, aligned quality thresholds, added lineage expectations |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
