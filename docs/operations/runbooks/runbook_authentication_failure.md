# Runbook — Authentication Failure

**Document Type:** Operational Runbook  
**Product:** FINDEX  
**Status:** Draft  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** Data Engineering Team  
**Classification:** Internal  

---

## 1. Purpose

This runbook provides procedures for responding to authentication failures when accessing external data sources.

---

## 2. Detection

- Pipeline alert: authentication error, HTTP 401/403
- Connector logs showing invalid credentials, expired token, or permission denied
- Monitoring: pipeline failure with auth error type

---

## 3. Diagnosis

1. Identify the specific authentication error from logs
2. Check credential expiration date
3. Verify if source institution rotated credentials or API keys
4. Check if access permissions changed on source side
5. Review any recent credential changes in FINDEX
6. Confirm if the issue affects one source or multiple sources

---

## 4. Containment

1. Do not attempt unlimited retries with invalid credentials
2. Alert Platform Admin and Technical Owner
3. Isolate affected connector
4. Document the failure in incident management

---

## 5. Recovery

### 5.1 Expired Credential

1. Retrieve new credential from source institution
2. Update credential in AWS Secrets Manager (production) or .env (development)
3. Verify new credential with test connection
4. Rerun pipeline with new credential
5. Verify successful ingestion
6. Update credential rotation schedule

### 5.2 Revoked or Changed Permission

1. Request restored or updated permissions from source institution
2. Review access requirements and update IAM roles
3. Verify new permissions with test connection
4. Rerun pipeline
5. Update access documentation

### 5.3 Token Expiration (OAuth/API Key)

1. Follow source's token refresh procedure
2. Update automated token refresh mechanism
3. Verify new token works
4. Rerun pipeline
5. Implement proactive token refresh before expiration

---

## 6. Validation

1. Test connection with new credentials
2. Run test ingestion
3. Verify data quality and completeness
4. Confirm no records were lost during outage
5. Check lineage integrity

---

## 7. Communication

- Alert Technical Owner and Platform Admin immediately
- Notify Data Owner if outage exceeds freshness SLA
- Document credential change in change log
- Update secrets management documentation

---

## 8. Prevention

1. Implement credential expiry monitoring and alerts
2. Set up automated credential rotation where supported
3. Maintain credential backup in secure vault
4. Document credential rotation procedures per source
5. Regularly test credential refresh mechanisms
6. Never commit credentials to version control

---

## 9. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft |

---

*This document is classified as Internal.*