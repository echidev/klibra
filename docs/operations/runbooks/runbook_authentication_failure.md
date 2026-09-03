# Runbook — Authentication Failure

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §11 (source catalog), §12 (source registration), §16 (security); TDD §13 (connector), §31 (security architecture)  

---

## 1. Purpose

Provide procedures for responding to authentication failures when accessing external data sources.

---

## 2. Detection

- Pipeline alert: authentication error, HTTP 401/403.
- Connector logs showing invalid credentials, expired token, or permission denied.
- Monitoring: pipeline failure with `error_type = AuthenticationFailure`.

---

## 3. Diagnosis

1. Identify the specific authentication error from logs.
2. Check credential expiration date.
3. Verify if source institution rotated credentials or API keys.
4. Confirm whether access permissions changed on the source side.
5. Review recent credential changes in the Source Catalog.
6. Determine if the issue affects one source or multiple sources.

---

## 4. Containment

1. Stop unlimited retries with invalid credentials.
2. Alert Platform Admin and Technical Owner.
3. Isolate affected connector.
4. Document the failure in the incident management system.

---

## 5. Recovery

### 5.1 Expired Credential

1. Retrieve new credential from the source institution.
2. Update the credential in **AWS Secrets Manager** (production) or `.env` (development).
3. Verify the new credential with a test connection.
4. Re‑run the pipeline with the new credential.
5. Verify successful ingestion and downstream quality checks.
6. Update credential rotation schedule in the Source Catalog.

### 5.2 Revoked or Changed Permission

1. Request restored or updated permissions from the source institution.
2. Review and update IAM roles if needed.
3. Verify new permissions with a test connection.
4. Re‑run the pipeline.
5. Update the Source Catalog with the new access details.

### 5.3 Token Expiration (OAuth / API Key)

1. Follow the source’s token refresh procedure.
2. Update the automated token refresh mechanism.
3. Validate the new token works.
4. Re‑run the pipeline.
5. Implement proactive token‑expiry monitoring.

---

## 6. Validation

1. Test the connection with the new credentials.
2. Run a test ingestion for a small timeframe.
3. Verify data quality and completeness.
4. Ensure lineage and metadata are recorded correctly.
5. Confirm no records were lost during the outage.

---

## 7. Communication

- Alert Technical Owner and Platform Admin immediately.
- Notify Data Owner if the outage exceeds the freshness SLA.
- Document the credential change in the Source Catalog and Change Management System.
- Communicate status updates to stakeholders via incident channel.

---

## 8. Prevention

1. Implement credential expiry monitoring and alerts.
2. Set up automated credential rotation where supported.
3. Maintain credential backup in a secure vault.
4. Document credential rotation procedures per source.
5. Never commit credentials to version control.

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; added token refresh, prevention steps, and clarified communication |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
