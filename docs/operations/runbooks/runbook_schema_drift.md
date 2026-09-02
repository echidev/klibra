# Runbook — Schema Drift

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for detecting, classifying, investigating, and responding to schema changes in external data sources.

---

## 2. Detection

- Automated schema validation fails during ingestion
- Connector detects missing fields, new fields, or type mismatches
- Data contract validation fails
- Airflow task fails with schema-related error

---

## 3. Classification

Classify the schema change per TDD Section 19:

| Change Class | Examples | Action |
|---|---|---|
| **Compatible** | New nullable field, metadata-only change | Accept; update schema; no consumer impact |
| **Potentially Breaking** | Type widening/narrowing, new required field, changed categorical values | Investigate; adapt transformation; validate before publication |
| **Breaking** | Removed field, semantic redefinition, structural incompatibility | Stop pipeline; investigate; controlled deployment required |

---

## 4. Investigation

### 4.1 Assess the Change

1. Retrieve the new source schema
2. Compare with previous schema version
3. Map changes to classification (compatible, potentially breaking, breaking)
4. Identify affected downstream datasets and fields
5. Assess impact on business definitions and metrics

### 4.2 Check Source Notification

1. Check if source institution announced the change
2. Review source documentation for updates
3. Contact source institution if change is undocumented
4. Document all findings

---

## 5. Containment

1. If breaking: halt pipeline to prevent publishing incorrect data
2. If potentially breaking: quarantine affected records pending resolution
3. Alert Technical Owner and Data Owner
4. Document the drift in incident management system

---

## 6. Resolution

### 6.1 Compatible Changes

1. Update connector to accept new fields
2. Update schema documentation
3. Update data dictionary if new fields have semantic meaning
4. Validate pipeline produces correct output
5. Publish with updated metadata

### 6.2 Potentially Breaking Changes

1. Adapt transformation logic
2. Update data contract if constraints change
3. Update data dictionary
4. Test in staging environment
5. Validate output against business expectations
6. Publish with documentation of changes

### 6.3 Breaking Changes

1. Initiate change management process (per governance/change_management_process.md)
2. Evaluate backward compatibility strategy
3. Update connector and transformation
4. Update data contract and data dictionary
5. Notify all affected consumers with minimum 14-day lead time
6. Prepare migration plan for consumers
7. Prepare rollback plan
8. Deploy following approval gate
9. Validate post-deployment

---

## 7. Validation

1. Verify schema matches updated contract
2. Run all data quality checks
3. Validate business rules
4. Verify lineage is updated
5. Confirm consumer access to updated data
6. Check for data gaps during the drift period

---

## 8. Communication

- Alert Technical Owner immediately upon detection
- Notify Data Owner within 1 hour
- Notify Business Owner for breaking changes
- Update Source Catalog with change details
- Document in change log

---

## 9. Prevention

1. Implement automated schema drift detection
2. Set up schema validation in pipeline
3. Monitor source documentation for changes
4. Maintain field mapping registry
5. Add schema change alerts to monitoring

---

## 10. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*