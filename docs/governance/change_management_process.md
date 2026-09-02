# FINDEX — Change Management Process

**Document Type:** Change Management Process  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Governance Team  
**Classification:** Internal  

---

## 1. Purpose

This document defines the controlled process for proposing, reviewing, approving, and implementing changes to critical definitions, schemas, quality thresholds, and data contracts across the FINDEX platform.

The process ensures that changes are visible, documented, reviewed, tested, and communicated — preventing unauthorized or untested modifications from reaching production.

---

## 2. Scope

This process covers changes to:

- Business definitions of data products
- Data dictionary field definitions and semantics
- Data contract schemas and quality thresholds
- Source mappings and canonical field definitions
- Pipeline transformation logic affecting output data
- Quality rules and severity classifications
- Ownership assignments
- Source configurations affecting data output
- Metadata structures and operational configurations

---

## 3. Change Classification

### 3.1 Breaking Changes

Changes that may affect downstream consumers or data integrity:

- Field removal or renaming
- Data type changes (widening/narrowing)
- Constraint relaxation or tightening
- Semantic redefinition of an existing metric
- Structural incompatibility in source schemas
- Quality threshold changes that could alter publication behavior
- Ownership reassignment

### 3.2 Non-Breaking Changes

Changes that do not affect downstream consumers:

- New nullable field additions
- Metadata-only changes
- Documentation updates
- New metric additions (new fields, not modifying existing)
- Non-breaking source additions

### 3.3 Classification Criteria

| Criterion | Breaking | Non-Breaking |
|---|---|---|
| Field removal | ✓ | |
| Field rename | ✓ | |
| Data type change | ✓ | |
| Constraint tightening | ✓ | |
| Constraint relaxation | ✓ | |
| Semantic change | ✓ | |
| New nullable field | | ✓ |
| New field addition | | ✓ |
| Documentation update | | ✓ |

---

## 4. Change Management Workflow

### 4.1 General Workflow

```text
1. Change Proposed
   ├── Submit change request with documentation
   ├── Classify as Breaking or Non-Breaking
   └── Describe rationale, impact, and scope
       ↓
2. Impact Assessment
   ├── Identify affected datasets and consumers
   ├── Assess backward compatibility
   ├── Estimate effort for consumer updates
   └── Document affected systems
       ↓
3. Data Governance Review
   ├── Review change against governance standards
   ├── Verify classification accuracy
   ├── Assess quality implications
   └── Approve or request modifications
       ↓
4. Business Owner Approval (for Breaking Changes)
   ├── Business Owner reviews consumer impact
   ├── Confirms business acceptance
   └── Approves or rejects
       ↓
5. Consumer Notification
   ├── Notify all affected consumers
   ├── Provide change details and timeline
   ├── Minimum 14 days lead time for Breaking Changes
   └── Document notification and acknowledgments
       ↓
6. Implementation
   ├── Implement change in staging environment
   ├── Update documentation and contracts
   ├── Version the change
   └── Run all validation tests
       ↓
7. Staging Validation
   ├── Verify change works correctly
   ├── Validate against staging data
   ├── Confirm no unintended side effects
   └── Data Owner signs off
       ↓
8. Approval Gate
   ├── Data Governance final approval
   ├── Change documented and versioned
   └── Production deployment scheduled
       ↓
9. Production Deployment
   ├── Deploy following CI/CD pipeline
   ├── Monitor for anomalies
   └── Confirm successful deployment
       ↓
10. Post-Deployment Verification
    ├── Verify data quality post-deployment
    ├── Confirm consumer access
    └── Document deployment completion
```

### 4.2 Breaking Change Additional Requirements

For Breaking Changes, the following additional steps apply:

- **Impact assessment** must be thorough and documented
- **Consumer notification** must have minimum 14 days lead time
- **Migration plan** must be provided for affected consumers
- **Rollback plan** must be prepared before deployment
- **Executive approval** may be required for high-impact changes
- **Version** of the definition must be preserved for historical reference

---

## 5. Change Request Format

Every change request must include:

| Field | Description |
|---|---|
| **Change ID** | Unique identifier (CHG-001 format) |
| **Title** | Brief description of the change |
| **Classification** | Breaking or Non-Breaking |
| **Dataset(s) Affected** | List of affected datasets |
| **Proposed By** | Name and role of proposer |
| **Date Proposed** | Date of submission |
| **Rationale** | Why the change is needed |
| **Impact Assessment** | Affected consumers, systems, and downstream effects |
| **Migration Plan** | How consumers transition to the change |
| **Rollback Plan** | How to revert if needed |
| **Classification Justification** | Why Breaking or Non-Breaking |
| **Priority** | Urgency level |
| **Target Date** | Desired implementation date |

---

## 6. Change Log

All changes are recorded in a version-controlled change log:

| Field | Description |
|---|---|
| **Change ID** | Unique identifier |
| **Date** | Date of change |
| **Description** | Summary of change |
| **Classification** | Breaking or Non-Breaking |
| **Affected Datasets** | Datasets impacted |
| **Approved By** | Approver name |
| **Status** | Proposed → Under Review → Approved → Implemented → Closed |
| **Consumer Notification Date** | When consumers were notified |
| **Deployment Date** | When deployed to production |

---

## 7. Source Change Management

External source changes (detected per TDD Section 48) follow a parallel but adapted process:

1. **Detection:** Schema drift, definition changes, frequency changes detected
2. **Classification:** Compatible, Potentially Breaking, or Breaking (per TDD Section 19)
3. **Investigation:** Assess impact on ingestion and downstream
4. **Breaking Changes:** Controlled investigation before downstream publication
5. **Communication:** Document source change and notify affected consumers
6. **Adaptation:** Update connector, transformation, and contracts
7. **Validation:** Test and validate adapted pipeline
8. **Publication:** Resume publishing with updated documentation

---

## 8. Escalation

| Situation | Escalation |
|---|---|
| Change request blocked > 5 business days | Escalate to Data Governance Lead |
| Disagreement on Breaking/Non-Breaking classification | Data Governance review and decision |
| Breaking change with critical business impact | Executive Management review |
| Unresolved consumer objection to change | Data Governance arbitration; Executive escalation if needed |

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — change management workflow, classification, request format, source change management |

---

## 10. Document Status

This Change Management Process is a draft artifact subject to stakeholder review and approval.

This document is a companion to:
- **Data Governance Policy** — governance framework
- **Data Dictionary** — definition management
- **Data Contracts** — contract change management
- **PRD** — change requirements (Section 23)
- **TDD** — source change management (Section 48)

---

*This document is classified as Internal. Distribution is restricted to authorized FINDEX team members and stakeholders.*