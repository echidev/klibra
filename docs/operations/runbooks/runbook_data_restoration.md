# Runbook — Data Restoration

**Document Type:** Operational Runbook  
**Product:** KLIBRA  
**Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Platform Engineering  
**Classification:** Internal  
**Related:** PRD §74 (DR strategy); TDD §45 (backup/restore), §82 (replay sequence)  

---

## 1. Purpose

Provide step‑by‑step procedures for restoring data after loss, corruption, or disaster in KLIBRA (TDD §45, §82).

---

## 2. Detection

- Monitoring alert for **data loss** (record count drop, missing partitions).
- **Data corruption** flagged by quality‑gate failures.
- **Storage layer** error (S3 access failure, PostgreSQL outage).
- **Pipeline failure** log indicating incomplete ingestion.
- **Downstream consumer** report of missing or stale data.

---

## 3. Containment

1. Halt further ingestion for affected dataset.
2. Identify the scope of data loss:
   - Which layers affected (Raw, Bronze, Silver, Gold)?
   - Which time periods / partitions affected?
   - Is the loss complete or partial?
3. Alert **Platform Admin** and **Technical Owner**.
4. Document the event in incident management.

---

## 4. Pre‑Restoration Checks

| Check | Action |
| --- | --- |
| **Raw integrity** | Verify whether raw data exists in S3 (content hashes). |
| **Replica availability** | Check replica availability (cross‑region S3 replication). |
| **Backup availability** | Check PostgreSQL backup and Terraform state backup. |
| **Code version** | Confirm pipeline code version that produced the missing data. |
| **Lineage records** | Inspect `metadata/` for lineage to understand the data flow. |

---

## 5. Restoration Paths

### Path A — Raw Exists (most common)

1. Verify raw data integrity via content hash.
2. Re‑run **Bronze** transformation from raw.
3. Re‑run **Silver** transformation from Bronze.
4. Re‑run **Gold** transformation from Silver.
5. Validate each layer before proceeding.
6. Publish to production with correct `effective_from`/`effective_to` (ADR‑007).
7. Record restoration run in metadata.

### Path B — Raw Missing or Corrupted

1. Restore raw from **cross‑region S3 replica** (if available).
2. If not available, re‑fetch from source API using the backfill procedure (Runbook‑Backfill).
3. Follow Path A.

### Path C — Metadata / PostgreSQL Corrupted

1. Restore PostgreSQL from **latest backup** (see Disaster Recovery doc).
2. Re‑run lineage reconstruction if needed.
3. Validate metadata against raw counts.
4. Resume normal operations.

---

## 6. Validation

1. Verify **record count** matches pre‑loss baseline (or backfill spec).
2. Run **quality checks** (P0/P1) – must pass.
3. Verify **lineage** is intact (OpenMetadata).
4. Spot‑check downstream **Gold data products** for correctness.
5. Monitor **freshness** SLA post‑restoration.
6. Record restoration outcome in incident ticket.

---

## 7. Communication

- Inform **Data Owner** and **Business Consumer** of the restoration outcome.
- Provide **timeline** of data restoration.
- Notify **downstream consumers** when corrected data is published.
- Update **incident ticket** with restoration details.

---

## 8. Post‑Restoration

1. Document lessons learned.
2. Update **disaster recovery** runbook if gaps found.
3. Review **backup schedule** and improve if needed.
4. Conduct **blameless post‑mortem** for major incidents (TDD §46).

---

## 9. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Engineering | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Platform Engineering | Updated for KLIBRA PRD v2.0 / TDD v2.0; added restoration paths, validation checks, and communication steps |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
