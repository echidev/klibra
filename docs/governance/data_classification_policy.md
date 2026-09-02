# FINDEX — Data Classification Policy

**Document Type:** Data Classification Policy  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Governance Team  
**Classification:** Internal  

---

## 1. Purpose

This Data Classification Policy establishes a standardized classification framework for all data within the FINDEX platform. Classification determines handling requirements, access controls, encryption standards, and distribution rules.

The policy ensures that all data is appropriately categorized and that handling requirements are proportional to the sensitivity and business impact of the data.

---

## 2. Scope

This policy applies to all data within the FINDEX platform:

- Raw source payloads and acquisition metadata
- Bronze, Silver, and Gold layer datasets
- Operational metadata and pipeline execution records
- Data contracts, dictionaries, and documentation
- Monitoring logs and audit records
- Infrastructure configuration and code

---

## 3. Classification Levels

### 3.1 Public

**Definition:** Data that can be freely shared with external parties without restriction.

**Examples:** Published statistical indicators from BPS, publicly available exchange rates, published policy rates.

**Handling Requirements:**
- No access restrictions
- Standard distribution permitted
- No special encryption required beyond standard infrastructure security
- Standard archival policies apply

### 3.2 Internal

**Definition:** Data intended for use by authorized FINDEX team members and approved downstream consumers. Not for external distribution.

**Examples:** Credit growth indicators, banking statistics, financial sector aggregates, macroeconomic composites, operational metadata.

**Handling Requirements:**
- Access restricted to authorized FINDEX personnel and approved consumers
- No external sharing without explicit approval
- Encryption in transit required
- Encryption at rest recommended
- Access logging required
- Internal distribution only

### 3.3 Confidential

**Definition:** Sensitive data requiring restricted access, enhanced encryption, and strict audit logging. Unauthorized disclosure could cause significant harm.

**Examples:** Individual-level financial data, proprietary source data under restrictive terms, unreleased strategic indicators, security credentials.

**Handling Requirements:**
- Strict access control with explicit authorization
- Encryption in transit mandatory
- Encryption at rest mandatory
- Full audit logging of all access
- No external distribution
- Minimum access count
- Regular access review
- Incident response plan for breaches

---

## 4. Classification Rules

### 4.1 Default Classification

1. All FINDEX data products default to **Internal** classification.
2. Only data explicitly classified as Public or Confidential deviates from the default.
3. Classification is determined by the Data Owner with Data Governance oversight.

### 4.2 Classification Determination

Classification is determined by considering:

| Factor | Assessment |
|---|---|
| **Source sensitivity** | How sensitive is the source institution's data? |
| **Content sensitivity** | Does the data contain personally identifiable or confidential information? |
| **Business impact** | What is the impact if this data is disclosed? |
| **Licensing terms** | Do source terms restrict distribution? |
| **Regulatory requirements** | Are there legal or regulatory restrictions on distribution? |
| **Consumer expectations** | What classification do consumers expect? |

### 4.3 FINDEX-Specific Rule

FINDEX intentionally does not ingest personally identifiable customer information, confidential customer banking records, or regulated credit decision data. As such, Confidential-classified data within FINDEX is limited to:

- Source data under restrictive licensing terms
- Unreleased strategic indicators
- Security credentials and secrets
- Audit logs containing sensitive operational details

### 4.4 Public Data Exception

Public data sources do not automatically make the resulting data product Public. The data product classification may be elevated to Internal based on:

- Aggregation with other datasets creating sensitive composites
- Source licensing restrictions on derived products
- Business sensitivity of the combined indicator
- Regulatory considerations

---

## 5. Classification Management

### 5.1 Assignment

1. Data Owner proposes classification for each dataset.
2. Data Governance reviews and approves classification.
3. Classification documented in Data Contract and metadata system.
4. Classification is a required field for every dataset.

### 5.2 Reclassification

Reclassification follows the change management process:

1. Data Owner proposes reclassification
2. Impact assessment for affected consumers
3. Data Governance review and approval
4. Consumer notification if downgrade occurs
5. Implementation following CI/CD pipeline
6. Metadata and access controls updated

### 5.3 Downgrading Restrictions

Downgrading classification (e.g., Internal → Public) requires:

- Explicit source institution permission (if applicable)
- Legal review of licensing terms
- Data Governance approval
- Consumer notification
- Documented rationale

Upgrading classification has no additional restrictions beyond standard change management.

---

## 6. Access Controls by Classification

| Control | Public | Internal | Confidential |
|---|---|---|---|
| Access restriction | None | Authorized personnel only | Restricted authorization |
| Encryption in transit | Recommended | Required | Required |
| Encryption at rest | Recommended | Recommended | Required |
| Audit logging | Recommended | Required | Required |
| Distribution | Internal and external | Internal only | Internal only with minimum access |
| Access review | Annually | Quarterly | Monthly |
| Approval for access | None | Data Owner | Data Owner + Data Governance |

---

## 7. Handling Requirements

### 7.1 Storage

| Classification | Storage Requirements |
|---|---|
| Public | Standard object storage |
| Internal | Standard object storage with encryption at rest |
| Confidential | Encrypted object storage with enhanced access controls |

### 7.2 Transfer

| Classification | Transfer Requirements |
|---|---|
| Public | Standard transfer |
| Internal | Encrypted transfer (TLS) |
| Confidential | Encrypted transfer with authenticated channels |

### 7.3 Disposal

| Classification | Disposal Requirements |
|---|---|
| Public | Standard retention and archival policies |
| Internal | Secure deletion per data retention policy |
| Confidential | Secure deletion with verification; minimum retention period applies |

---

## 8. Classification Documentation

Every dataset's Data Contract must document:

| Field | Description |
|---|---|
| **Classification** | Public, Internal, or Confidential |
| **Rationale** | Why this classification was assigned |
| **Handling requirements** | Specific handling rules |
| **Access restrictions** | Who can access and under what conditions |
| **Review date** | When classification was last reviewed |

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — classification levels, determination rules, access controls, handling requirements |

---

## 10. Document Status

This Data Classification Policy is a draft artifact subject to stakeholder review and approval.

This document is a companion to:
- **Data Governance Policy** — governance framework
- **Access Review Process** — access controls by classification
- **PRD** — security and governance requirements (Section 16)
- **TDD** — security architecture (Section 31)

---

*This document is classified as Internal. Distribution is restricted to authorized FINDEX team members and stakeholders.*