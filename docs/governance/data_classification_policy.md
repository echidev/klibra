# KLIBRA — Data Classification Policy

**Document Type:** Data Classification Policy  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §16, §33; TDD §31  

---

## 1. Purpose

This Data Classification Policy establishes a standardized classification framework for all data within the KLIBRA platform. Classification determines handling requirements, access controls, encryption standards, audit obligations, and distribution rules (PRD §16, §33).

---

## 2. Scope

This policy applies to all data within KLIBRA:

- Raw source payloads.
- Bronze, Silver, Gold, Quarantine, and Metadata layers.
- Semantic metrics and intelligence products.
- Operational metadata and audit logs.
- Pipeline code, configuration, and infrastructure definitions.

---

## 3. Classification Levels

### 3.1 Public

**Definition:** Data explicitly published by authoritative institutions for unrestricted public access.

**Examples:** World Bank Indicators, IMF published statistics, FRED public series, ECB published series.

**Handling:**

- No access control beyond platform authentication.
- Permitted for broad internal and approved external consumption.
- Source terms and licensing constraints respected (PRD §38).

### 3.2 Internal

**Definition:** Data intended for use by authorized KLIBRA team members and approved downstream consumers. Not for external distribution.

**Examples:** Standardized Silver/Gold tables, semantic metrics, intelligence products, operational metadata.

**Handling:**

- Access restricted to authorized KLIBRA personnel and approved consumers.
- Encryption in transit required.
- Encryption at rest where supported (PRD §33).
- Audit logging of administrative actions.
- Versioning policy enforced.

### 3.3 Confidential

**Definition:** Data that, if disclosed without authorization, could cause reputational, competitive, or operational harm. Includes credentials, internal incident reports, and contractual details.

**Examples:** API keys, secrets, source redistribution agreements, internal incident reports.

**Handling:**

- Access restricted to a named, approved group with documented business justification.
- Encryption in transit and at rest mandatory.
- Audit logging mandatory; rotation policy enforced.
- Distribution prohibited.

### 3.4 Restricted

**Definition:** Reserved for future use cases that may require handling of personally identifiable information, regulated financial records, or transaction-level detail. Not applicable to current KLIBRA scope (PRD §5).

**Note:** KLIBRA explicitly avoids Restricted-classified data in its initial scope.

---

## 4. Classification Determination

### 4.1 Default

All KLIBRA data products default to **Internal** classification (PRD §33; TDD §31).

### 4.2 Determination Rules

Classification is determined by:

- Source institution's terms of use.
- Whether data contains personally identifiable information (PII).
- Whether data is subject to redistribution restrictions.
- Contractual obligations with sources.
- Operational sensitivity (e.g., credentials, incident reports).

### 4.3 KLIBRA-Specific Rule

KLIBRA is designed for **public / non-confidential economic data** (PRD §33). The platform intentionally does not ingest:

- Personally identifiable customer information.
- Confidential customer banking records.
- Regulated credit-decision data.
- Transaction-level financial data.

Confidential classification within KLIBRA is therefore limited to:

- Secrets and API keys.
- Internal incident reports.
- Source redistribution agreements.
- Audit logs containing sensitive operational detail.

---

## 5. Required Fields per Classification

Each dataset must declare its classification in its data contract (PRD §29; TDD §66):

| Field | Public | Internal | Restricted (future) |
| --- | --- | --- | --- |
| **classification** | Required | Required | Required |
| **source_terms** | Required | Required | Required |
| **redistribution_allowed** | Yes | Per source terms | No |
| **encryption_in_transit** | Required | Required | Required |
| **encryption_at_rest** | Where supported | Required | Required |
| **access_role_required** | Any role | Authenticated | Specific named roles |
| **audit_logging** | Standard | Standard | Enhanced |
| **retention_policy** | Per source terms | Per retention policy | Per regulatory requirement |

---

## 6. Access Controls

Aligned with `access_review_process.md` (TDD §51):

| Classification | Default Roles |
| --- | --- |
| Public | All authenticated roles |
| Internal | Platform Admin, Data Engineer, Data Analyst, Data Scientist, Business Consumer, Read-only Auditor |
| Confidential | Platform Admin, Technical Owner (named) |
| Restricted (future) | Named individuals with documented justification |

---

## 7. Handling Requirements

### 7.1 Storage

- **Public:** Object storage with standard encryption.
- **Internal:** Object storage + RDS; access logging enabled; least-privilege IAM.
- **Confidential:** Object storage + Secrets Manager; rotation policy; audit logs retained ≥ 1 year.

### 7.2 Transit

- TLS 1.2+ for all data movement.
- mTLS for service-to-service communication where supported.

### 7.3 Distribution

- **Public:** May be redistributed per source terms.
- **Internal:** Internal use only.
- **Confidential:** No external distribution.

### 7.4 Logging

- All read access to Confidential and Restricted data is logged.
- Logs retained per audit requirements (PRD §33).

---

## 8. Compliance

KLIBRA must comply with:

- Source institutions' terms of use.
- Provider redistribution policies (PRD §38).
- Applicable data-protection regulations (where applicable).

Public data does not imply unrestricted commercial redistribution — provider terms must be honored (PRD §38).

---

## 9. Classification Updates

Changing the classification of an existing dataset is a **Major change** under `change_management_process.md` and requires:

1. New classification rationale documented.
2. Data Governance review.
3. Updated data contract.
4. Consumer communication.
5. Audit-log entry.

---

## 10. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Re-aligned to KLIBRA PRD v2.0 / TDD v2.0; clarified KLIBRA is public-data-only and Confidential scope is limited to secrets, incident reports, source agreements |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
