# Production Readiness Review — Checklist (TDD §59, PRD §37)

Use this checklist before declaring KLIBRA production-ready.

## Architecture
- [ ] Architecture documented (TDD, ADRs)
- [ ] Failure paths documented (runbooks)
- [ ] Dependencies identified (service map)
- [ ] No KNOWN missing cross-references to PRD/TDD

## Sources
- [ ] Source catalog live-verified for all Release 1 sources (World Bank, ECB, FRED)
- [ ] Source contracts validated against `source-contract.schema.json` (TDD §66)
- [ ] Quarantine path exercised for a simulated failure

## Data
- [ ] SCD-2 invariant covered by contract tests
- [ ] Point-in-time semantics demonstrated end-to-end
- [ ] Silver quality gates exercised for a real ingestion run

## Semantic / Intelligence
- [ ] At least one semantic metric promoted and version-controlled
- [ ] Consumers receive a published metric version + deprecation policy
- [ ] Intelligence products validated for explainability and coverage

## Operations
- [ ] Runbooks cover the 10 required scenarios (TDD §47)
- [ ] Monitoring covers the 9 data-pipeline SLAs/SLOs (PRD §32–§34)
- [ ] Incident workflows tested end-to-end (TDD §46)

## Security
- [ ] Secret scan (`gitleaks`) passes
- [ ] `.env.example` populated; no secrets in repo
- [ ] Branch protection on `main` with required reviews

## Deployment
- [ ] `docker compose up -d` brings up the full local dev stack
- [ ] CI green on `main` (format/lint → unit → contract → dbt → infrastructure → build)
