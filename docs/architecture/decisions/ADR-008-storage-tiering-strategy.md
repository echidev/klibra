# ADR-008 — Storage Tiering Strategy

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §60 (cost governance), §72 (cost management); TDD §44 (cost management), §50 (retention), §70 (revision preservation)  

---

## Context

KLIBRA stores multi‑year economic and market data across Raw, Bronze, Silver, and Gold layers. Access patterns vary: recent data is queried frequently; older data is accessed rarely. Storage cost must be controlled while preserving data for historical reconstruction (PRD §60, §72; TDD §44, §50).

---

## Decision

Adopt a **four‑tier storage strategy** with automatic lifecycle transitions based on data age and access patterns:

| Tier | Storage Class | Transition Trigger | Retention |
| --- | --- | --- | --- |
| **Hot** | S3 Standard | Immediate (active data) | 0–90 days |
| **Warm** | S3 Standard‑IA (Infrequent Access) | After 90 days | 90 days–2 years |
| **Cold** | S3 Glacier / Glacier Deep Archive | After 2 years | 2–10 years |
| **Archive** | S3 Glacier Deep Archive (compliance) | After 10 years | Per retention policy |

- **Raw layer** is exempted from aggressive tiering to preserve full source history for the longest feasible period (TDD §7, §70).
- **Bronze, Silver, Gold** follow the tier schedule.
- **Quarantine** retains data for a shorter period (90 days hot, then purged after investigation, per Runbook‑Quality‑Failure).
- **Operational metadata (PostgreSQL)** uses automated RDS snapshots (30 days retention) with cross‑region backup.

---

## Alternatives Considered

- **Single storage tier (S3 Standard only)** – Rejected. Highest cost; not sustainable for long‑term retention.
- **Manual tiering** – Rejected. Error‑prone, labour‑intensive, inconsistent.
- **Two‑tier (Standard + Glacier)** – Rejected. Insufficient control over intermediate “warm” period.
- **Four‑tier (selected)** – Balanced: cost‑optimised, automated, preserves access for analytical queries on recent data.

---

## Implementation Details

- Lifecycle policies defined per layer in Terraform (`infrastructure/terraform/s3.tf`).
- `Effective_from` / `effective_to` (ADR‑007) allow re‑hydration of cold data into warmer tiers when needed without loss.
- Monitoring tracks data growth, tier transition counts, and estimated cost per layer (Runbook‑Monitoring‑Alerts).
- Retention adjustments require approval per the change management process (`docs/governance/change_management_process.md`).

---

## Consequences

**Positive:**

- Significant cost reduction for historical data.
- Automated lifecycle management reduces operational burden.
- Compliance with retention policy is verifiable.
- Raw layer protected by policy exemption ensures full source history.

**Negative:**

- Retrieval latency for cold data (minutes to hours); acceptable for batch analytics, not for real‑time.
- Requires monitoring of transition success to detect mis‑configurations.

---

## Definition of Done

- Lifecycle policies applied to all S3 buckets (Raw exempt, others per schedule).
- Monitoring dashboard shows tier distribution and cost per layer.
- Documentation updated in `docs/operations/monitoring_alerts.md` and `docs/operations/disaster_recovery.md`.
- Review sign‑off from Data Governance and Platform Admin.
