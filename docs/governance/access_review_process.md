# FINDEX — Access Review Process

**Document Type:** Access Review Process  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Governance Team  
**Classification:** Internal  

---

## 1. Purpose

This document defines the process for reviewing and managing access to FINDEX datasets and platform components. It ensures that access adheres to the least privilege principle and that access rights remain appropriate over time.

---

## 2. Scope

This process covers access to:

- Object storage (S3/MinIO) — all layers
- Relational metadata (PostgreSQL)
- Orchestration platform (Airflow)
- Analytics and serving layers (Athena, BI tools, APIs)
- Pipeline code and infrastructure
- Monitoring and alerting systems
- Operational metadata and logs

---

## 3. Role-Based Access Model

### 3.1 Roles

| Role | Access Level | Description |
|---|---|---|
| **Platform Admin** | Full platform access | Infrastructure management, IAM, security configuration |
| **Data Engineer** | Pipeline development, staging/production read | Builds and maintains pipelines; read access to all layers |
| **Data Analyst** | Curated datasets read access | Query and analyze Silver/Gold datasets |
| **Data Scientist** | Historical datasets and features read access | Model training and feature engineering |
| **Business Consumer** | Data product read access | Access to Gold data products only |
| **Read-only Auditor** | Audit logs and metadata | No data modification; audit and compliance review |

### 3.2 Access Matrix

| Resource | Platform Admin | Data Engineer | Data Analyst | Data Scientist | Business Consumer | Read-only Auditor |
|---|---|---|---|---|---|---|
| Raw layer | Read/Write | Read/Write | No access | No access | No access | Read |
| Bronze layer | Read/Write | Read/Write | No access | No access | No access | Read |
| Silver layer | Read/Write | Read/Write | Read | Read | No access | Read |
| Gold layer | Read/Write | Read/Write | Read | Read | Read | Read |
| Metadata (PostgreSQL) | Full | Full | Read | Read | No access | Read |
| Orchestration (Airflow) | Full | Full | No access | No access | No access | Read |
| Pipeline code | Read/Write | Read/Write | No access | No access | No access | Read |
| Infrastructure (Terraform) | Full | Full | No access | No access | No access | No access |
| Monitoring | Full | Full | Read | Read | Read | Read |
| Secrets | Full (via Secrets Manager) | No direct access | No access | No access | No access | No access |
| Audit logs | Read | Read | No access | No access | No access | Read |

### 3.3 Production Write Restrictions

Production write privileges are restricted to:

- Authorized pipeline services (via IAM roles)
- Platform Admin for emergency interventions (with approval and audit trail)
- No individual has direct production write access through ad-hoc tools

---

## 4. Access Review Process

### 4.1 Review Cadence

| Review Type | Frequency | Owner |
|---|---|---|
| Access grant review | Quarterly | Platform Admin + Data Governance |
| Access recertification | Quarterly | Data Owner (per dataset) |
| Privilege escalation review | Per escalation | Platform Admin |
| Emergency access review | Monthly | Platform Admin + Data Governance |
| Full access audit | Annually | Data Governance + Security |

### 4.2 Access Grant Process

```text
1. Access request submitted by individual
   ↓
2. Manager and Data Owner approval
   ↓
3. Least privilege assessment
   ↓
4. Access granted with defined scope and expiration
   ↓
5. Access recorded in access registry
   ↓
6. Periodic review (quarterly)
```

### 4.3 Access Recertification

Each quarter, all access grants are reviewed:

1. **Notification:** All access holders notified 2 weeks before review
2. **Self-attestation:** Access holders confirm their access is still required
3. **Manager approval:** Managers confirm access is appropriate
4. **Data Owner approval:** Data Owners confirm dataset access is appropriate
5. **Removal:** Access not recertified is revoked
6. **Documentation:** Review outcomes documented

### 4.4 Access Revocation

Access must be revoked promptly when:

- Role changes
- Team member departure
- Access grant expires
- Access recertification fails
- Security incident detected

Revocation must occur within 1 business day of the triggering event.

---

## 5. Access Registry

### 5.1 Registry Contents

The access registry maintains:

| Field | Description |
|---|---|
| **User/Service ID** | Unique identifier |
| **Role** | FINDEX role assignment |
| **Resource** | Resource accessed |
| **Access Level** | Read, Write, Full |
| **Grant Date** | When access was granted |
| **Expiration Date** | When access expires (if applicable) |
| **Last Reviewed** | Date of last recertification |
| **Status** | Active, Expired, Revoked |
| **Granted By** | Who authorized the access |
| **Business Justification** | Reason for access |

### 5.2 Registry Maintenance

- Updated on every access grant, modification, or revocation
- Reviewed quarterly during access recertification
- Archived records retained per audit requirements
- No credentials stored in the registry

---

## 6. Least Privilege Enforcement

1. **Default deny:** Access is denied by default; explicitly granted only when required.
2. **Scope minimization:** Grants specify the minimum resource scope and access level.
3. **Time-bounded access:** Temporary access has defined expiration dates.
4. **Separation of duties:** Critical operations require multiple individuals.
5. **Service accounts:** Pipeline services use IAM roles, not individual credentials.
6. **No shared credentials:** Each individual has unique, attributable access.

---

## 7. Emergency Access

Emergency access follows a separate process:

1. Request justification and scope
2. Platform Admin approval
3. Time-bounded grant (maximum 4 hours)
4. Full audit logging of all actions
5. Immediate revocation after emergency resolved
6. Post-incident review of emergency access usage

---

## 8. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — access review process, role-based access model, recertification, least privilege enforcement |

---

## 9. Document Status

This Access Review Process is a draft artifact subject to stakeholder review and approval.

This document is a companion to:
- **Data Governance Policy** — access governance requirements
- **Data Classification Policy** — access based on classification
- **PRD** — security and governance requirements (Section 16)
- **TDD** — security architecture (Section 31) and access model (Section 51)

---

*This document is classified as Internal. Distribution is restricted to authorized FINDEX team members and stakeholders.*