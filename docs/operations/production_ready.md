# Production Readiness Review — Checklist (TDD §59, PRD §37)

Use this checklist before declaring KLIBRA production-ready (R4, 002-F T058).

## Architecture
- [ ] Architecture documented (TDD, ADRs incl. 001 ADR-001..008)
- [ ] Failure paths documented (runbooks, incl. DR drill runbook T055)
- [ ] Dependencies identified (service map)

## Sources (R1 + R2 set)
- [ ] Source catalog live-verified: World Bank, ECB, FRED (PRD §10.1 gate)
- [ ] Source contracts validated against `source-contract.schema.json` for all
      promoted sources (TDD §66)
- [ ] Class C portal/account path validated for IMF before promotion (TDD §13.3)
- [ ] Quarantine path exercised for a simulated failure

## Data
- [ ] SCD-2 invariant covered by contract tests (`tests/silver/test_scd2_invariant.py`)
- [ ] Point-in-time semantics demonstrated end-to-end (002 `point_in_time.py`)
- [ ] Silver quality gates exercised for a real ingestion run
- [ ] Schema fingerprint change classification present (TDD §19, `schema_fingerprint.py` T051)
- [ ] Cross-source reconciliation unit tests pass (002-E T044)

## Semantic / Intelligence
- [ ] At least one semantic metric promoted and version-controlled (002-C)
- [ ] 8 metrics registered in `metric_registry` (TDD §63)
- [ ] Intelligence layer: 5 products imported and deterministic (002-D)
- [ ] Intelligence products respected version-bump policy (TDD §61.3, `test_methodology_bump.py`)
- [ ] Consumers receive metric version + deprecation policy (FR-7 002-C)

## Operations
- [ ] Runbooks cover the 10 required scenarios + DR drill (TDD §47, T055)
- [ ] Monitoring covers the 9 data + pipeline SLAs/SLOs (PRD §32–§34)
- [ ] Per-dataset cost telemetry wired via OpenMetadata + CloudWatch (T056)
- [ ] Backfill orchestrator validates + enforces idempotency (T053)
- [ ] Incident workflows tested end-to-end (TDD §46)

## Security
- [ ] Secret scan (`gitleaks`) passes
- [ ] `.env.example` populated; no secrets in repo (AGENTS.md §6.1)
- [ ] Branch protection on `main` with required reviews (AGENTS.md §10)

## Deployment
- [ ] `docker compose up -d` brings up the full local dev stack (MinIO, Postgres, Airflow)
- [ ] CI green on `main` (format/lint → unit → contract → dbt → infrastructure → build)
- [ ] A failure drill has been executed and recorded (PRD §37 #20, T055)

## Evidence
- [ ] This checklist is reviewed and approved by the Data Governance Committee.
