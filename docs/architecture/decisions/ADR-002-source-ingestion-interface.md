# ADR-002 — Source Ingestion Interface

**Status:** Accepted  
**Date:** 2026-09-03  
**Author:** KLIBRA Data Platform Engineering  
**Deciders:** KLIBRA Architecture Team  
**Supersedes:** None  
**Related:** PRD §12 (source registration); TDD §13 (ingestion architecture)  

---

## Context

KLIBRA must ingest data from heterogeneous external sources (World Bank, IMF, FRED, ECB, Alpha Vantage, CoinGecko). Sources differ in access mechanisms, authentication, data formats, schedules, and rate limits (PRD §10.1, TDD §13). Ingestion must be modular, testable, and replayable while preserving raw payloads (TDD §2.1, §3.1).

---

## Decision

Each source connector shall implement a **common interface** conceptually equivalent to:

```text
discover()               # List available datasets / endpoints
authenticate()           # Obtain/refresh credentials (if needed)
extract()                # Retrieve payload(s) for a specific period
validate_response()      # Verify HTTP status, schema, checksum
persist_raw()            # Write immutable payload to `raw/` layer with manifest
emit_metadata()         # Record run_id, timestamps, source_version, payload_hash
```

Connector code shall contain **no downstream business logic**; business rules reside in later pipeline layers (Bronze/Silver/Gold) per TDD §13.1.

---

## Alternatives Considered

- **Monolithic Ingestion Service** — Rejected. Tight coupling, single point of failure, hard to test.
- **Standardized Connector Interface (Selected)** — Modular, extensible, supports per‑source authentication, compatible with Airflow DAG design (TDD §25).
- **Message‑Queue Based Ingestion** — Rejected. Adds unnecessary complexity for batch‑oriented scheduled ingestion.

---

## Implementation Details

- Connectors are Python packages under `ingestion/` (e.g., `ingestion/worldbank/`).
- Configuration (access class, endpoint, credential source) stored in the **Source Catalog** (`docs/data/source_catalog.md`).
- Credential handling uses **AWS Secrets Manager** (prod) or `.env` (dev) as defined in TDD §32.
- Idempotency keys (TDD §15) are derived from `source_id`, `dataset_id`, `source_period`, `source_version`, `payload_hash` to guarantee exactly‑once ingestion.
- All connectors are unit‑tested (Test Strategy §1) and registered in the Airflow DAG `discover -> extract` sequence (TDD §13, ADR‑004).

---

## Consequences

**Positive:**

- Clear contract for new connectors.
- Simplifies testing and CI validation.
- Enables per‑source credential rotation without pipeline changes.
- Facilitates backfills using the same interface (Runbook‑Backfill).

**Negative:**

- Requires disciplined separation of concerns; risk of embedding business rules in connectors mitigated by code review and static analysis.

---

## Definition of Done

- All existing source connectors (World Bank, IMF, FRED, ECB, Alpha Vantage, CoinGecko) implement the interface.
- Unit tests cover each method with success and failure paths.
- Documentation added to `docs/operations/runbooks/` for troubleshooting.
- Airflow DAG updated to use the new interface.
- Review sign‑off from Data Governance (access control) and Technical Owner.
