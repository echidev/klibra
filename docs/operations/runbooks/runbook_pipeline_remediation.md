# Runbook — E2E Pipeline Remediation (Spec 004)

1. **Detect** — raw not persisted: `log_event ... raw write failed` (service=klibra-orchestration, level=ERROR, `trace_id`, `run_id`).
   - Gold row counts: `gold fan-out complete` `details.row_counts` is `{k:0}` for all products.
   - Quarantine: `quarantine_records_total` spike or `apply_quality_gate` returns `quarantine_count > 0`.
   - Backfill: `BackfillOrchestrator.validate` log REJECTED with `errors=[]` reasons.
2. **Diagnose** — verify env `KLIBRA_ENV`, `MINIO_*`/`AWS_*`, bucket existence, MinIO liveness (`/minio/health/ready`), `run_results.json` path.
3. **Contain** — rerun affected DAG task via Airflow UI; idempotency key prevents duplicate raw objects.
4. **Recover** — trigger backfill via CLI or DAG task; re-extract uses same `run_id` guarded by content hash.
5. **Validate** — `pytest tests/integration/test_storage_mandatory.py -q` and `-k "not e2e"`; quickstart steps in `specs/004-e2e-pipeline-remediation/quickstart.md`.
6. **Communicate** — incident severity per PRD incident matrix; notify `data-platform` owner.
