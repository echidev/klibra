# ADR-009 — Mandatory Raw Storage & Quarantine Routing

- **Status**: Accepted
- **Date**: 2026-09-06
- **Scope**: `ingestion/storage/` · `orchestration/{tasks,dags/klibra_pipeline}`
- **Context**: Gap analysis (004) found two gaps vs. Constitution Principles I, IV, XII:
  1. `run_extraction(storage_writer=None)` made raw persistence optional, violating **Source Fidelity (I)**.
  2. `apply_quality_gate` raised on `QUARANTINED/REJECTED` instead of routing to a quarantine layer, violating **Data Quality by Design (IV)**.
  3. `build_gold` had two divergent return shapes (legacy fast-path vs dbt), forcing downstream branching.
- **Decision**:
  1. Make raw storage mandatory: `run_extraction` now requires `storage_writer` and `storage_client` (fail-fast `RuntimeError`).
  2. Drive storage via a single env key `KLIBRA_ENV` (`development` → MinIO via `MINIO_*`, else boto3 via `AWS_*`).
  3. Route `QUARANTINED` records through `QuarantineStorageWriter` into `quarantine/source={id}/dataset={id}/run_id={id}/{obs_id}.json`; weight failures remain warning-only.
  4. Keep quarantine write failure-isolated: it never breaks the main pipeline; only a `WARN` log is emitted (contracts/quarantine.md).
  5. Normalize `build_gold` to a 5-key return on both paths (`status`, `records`, `products`, `row_counts`, `run_id`) via `_parse_gold_row_counts` and fix `publish_gold` to accept either `records` or `row_counts`.
  6. Wire storage into the DAG at the `extract` task; expose backfill via an Airflow task + CLI.
- **Consequences**:
  - CI tests must use an in-memory `ObjectClient` instead of relying on "no storage" mode.
  - Additional quarantine bucket metrics (`storage_writes_total`, `quarantine_records_total`, `gold_row_counts_correctness_total`) instrumented in `orchestration/metrics/pipeline.py`.
  - Backward-compat maintained: legacy fast-path shape now derives `products`/`row_counts` from `len(records)`.
- **Alternatives considered**: Introducing a `KLIBRA_STORAGE_TYPE` toggle (rejected — duplicates `KLIBRA_ENV` semantics); making quarantine a Gold product (rejected — violates quarantine as Silver hygiene layer).
