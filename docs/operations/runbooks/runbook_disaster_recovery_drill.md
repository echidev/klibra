# Runbook: Disaster Recovery Drill

**Audience:** Data Platform team, Data Governance Committee.
**Trigger:** Quarterly (recommended) or after any major platform change.
**Per:** PRD §37 #20, TDD §45.

## Goal

Verify that KLIBRA can be fully restored from immutable Raw + versioned
transformations + Postgres control plane, with **no manual editing of
production data**.

## Pre-flight (T-1)

- [ ] All upstream source providers are reachable.
- [ ] `main` branch of repo is at a known commit.
- [ ] Last successful ingestion timestamp per active source is recorded.
- [ ] Last successful publish timestamp per Gold product is recorded.
- [ ] Local Postgres + MinIO stack is up (`docker compose up -d`).
- [ ] `python-dotenv` is loaded and `.env` contains no production keys.

## Detection

The drill is detected by the orchestration scheduler (`orchestration/dags/klibra_pipeline.py`):

- After 7 days without a `PipelineDrillScheduled` event, the pipeline
  emits a `PipelineDrillNeeded` alert.
- The Data Governance Committee is paged via the alert router.

## Diagnosis

- Confirm the last 4 successful ingestion runs per source are recorded
  in `run_history` (Postgres).
- Confirm the last 4 successful publish events per Gold product in
  `fact_intelligence_score` lineage (`lineage_ref`).
- If any of these are missing, the drill cannot run; the platform is
  genuinely degraded (handle as P0 production incident).

## Containment

- Take a one-time snapshot of the current MinIO bucket set
  (`s3://klibra-data-*`).
- Do not pause production ingest during the drill (drill is
  non-blocking).
- Tag the current `main` commit as `drill-NNN-YYYYMMDD` for
  reproducibility.

## Recovery

- Drop the Postgres schema and re-run `alembic upgrade head`.
- Drop MinIO buckets; re-ingest via the `klibra_pipeline` DAG from the
  last successful `run_id` per source (idempotency keys make this safe).
- Re-emit Gold products from Silver; the dbt models are deterministic
  per `effective_to` SCD-2 logic.
- Verify `gold_macro_indicators` row count matches the pre-drill baseline
  (compare to the recorded timestamp).

## Validation

- [ ] All 6 Release 1 sources re-ingested; row counts within 1% of baseline.
- [ ] All 5 Gold products rebuilt; `effective_to IS NULL` count matches
      the pre-drill value.
- [ ] At least one intelligence product re-emitted (e.g.
      `intelligence_market_stress`).
- [ ] Lineage records emitted per TDD §69.

## Communication

- Notify DGC, Platform Admin, and Data Owner within 1h of drill
  start.
- Publish a `docs/operations/drills/drill-NNN-YYYYMMDD.md` summary at
  completion.
- Update PRD §37 #20 evidence.

## Prevention

- Schedule the drill quarterly in Airflow (`@quarterly` schedule in
  the `klibra_drill` DAG).
- Rehearse the drill on a fresh environment once per year.
- Track drill duration; alert if it exceeds 4h.
