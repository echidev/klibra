# KLIBRA — Economic Intelligence Platform

Enterprise-grade governed platform that consolidates approved public economic data sources, preserves source-level history, standardizes heterogeneous datasets, applies measurable data-quality controls, and exposes curated data products for downstream consumption.

## Overview

KLIBRA is a governed enterprise economic intelligence platform that converts heterogeneous public economic and market observations into trusted data products, reusable semantic metrics, and explainable intelligence products.

The initial domain is the global economic and financial ecosystem, with emphasis on:

- Credit and lending intelligence
- Financial-sector monitoring
- Macroeconomic context
- Regional financial intelligence
- Risk and strategy analysis

## Features

- Ingest from public APIs: World Bank, ECB, FRED, IMF, Alpha Vantage, CoinGecko
- Preserve raw source payloads immutably (content-hash, manifest, lineage)
- Bronze / Silver / Gold / Quarantine / Metadata lakehouse layers
- Canonical observation model (`fact_economic_observation`) with SCD-2 temporal handling
- Automated data-quality checks with P0/P1 quarantine blocking
- dbt-based Silver and Gold transformations
- Semantic metric definitions (grain, formula, version, owner, source policy)
- Composite intelligence products with explainability and coverage/confidence
- Full lineage from Gold → Silver → Bronze → Raw → Source (OpenMetadata)
- Structured JSON logging and pipeline observability

## Quick Start

```bash
# Clone
git clone git@github.com:echidev/klibra.git
cd klibra

# Python 3.11+ required (dev machine uses 3.14)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start local dev environment
docker compose up -d

# Open Airflow UI
# http://localhost:8080
```

## Repository Structure

```text
KLIBRA/
├── docs/
│   ├── product/           # PRD
│   ├── technical/         # TDD
│   ├── architecture/      # ADRs
│   ├── governance/        # policies, ownership, glossary, quality
│   ├── data/              # source catalog, contracts
│   └── operations/        # runbooks, CI/CD, monitoring, DR
├── ingestion/
│   ├── connectors/        # source connectors (worldbank, ecb, fred, ...)
│   ├── util/              # manifest, idempotency, logging, env
│   └── storage/           # raw storage writers (S3/MinIO)
├── transformation/
│   ├── bronze/            # source-aligned parsing
│   ├── silver/            # dbt canonical model
│   └── gold/              # consumer-oriented data products
├── semantic/              # metric registry, point-in-time, contracts
├── intelligence/          # composite intelligence products
├── orchestration/
│   ├── dags/              # Airflow DAGs
│   ├── util/              # run_state, cost, env
│   ├── metrics/           # pipeline + data plane metrics
│   ├── alerts/            # severity-based alert routing
│   └── operators/         # custom Airflow operators (backfill)
├── tests/                 # unit, contract, integration, e2e, failure
├── infrastructure/
│   ├── docker/            # Dockerfile, docker-compose.yml
│   ├── postgres/          # schema migrations
│   ├── openmetadata/      # catalog/lineage config
│   ├── terraform/         # cloud infra (S3, IAM, Glue, Athena, ...)
│   └── airflow/           # Airflow config
├── scripts/               # venv_autosource.sh, utility scripts
├── specs/                 # feature specifications (gitignored)
└── AGENTS.md              # agent operating contract (gitignored)
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Key configuration:

| Variable | Purpose |
|---|---|
| `KLIBRA_ENV` | `development`, `staging`, or `production` |
| `POSTGRES_*` | PostgreSQL connection for control plane |
| `AWS_S3_BUCKET_*` | Bucket names per lakehouse layer |
| `MINIO_*` | MinIO config for local development |
| `FRED_API_KEY` | FRED API key (Class B source) |
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage API key (Class B source) |
| `COINGECKO_DEMO_API_KEY` | CoinGecko Demo API key (Class B source) |

**Never commit `.env` to version control.** (AGENTS.md §6.1)

## Architecture Overview

```text
External Sources (World Bank / ECB / FRED / IMF / AV / CoinGecko)
        │
    Source Connector (discover → authenticate → extract →
                      validate_response → persist_raw → emit_metadata)
        │
    Raw (immutable, content hash)
        │
    Bronze (source-aligned)
        │
    Quality Gate (P0/P1 blocking → quarantine)
        │
    Silver (canonical fact_economic_observation + dimensions)
        │
    Gold (gold_macro_indicators, gold_interest_rate_monitor, ...)
        │
    ┌────────────┼────────────┐
    │            │            │
Semantic   Intelligence    Consumer API
Layer      Products        / BI / Notebooks
```

## Release Strategy

| Release | Scope |
|---|---|
| 0 — Foundation | Repository standards, source catalog, environment, baseline orchestration |
| 1 — Trusted Data Foundation | World Bank, ECB, one Class B source; Raw → Bronze → Silver → Gold |
| 2 — Multi-Source Intelligence | IMF, additional source, cross-source reconciliation, country benchmark, semantic metrics |
| 3 — Intelligence Layer | Composite intelligence products, explainable scorecards, semantic API |
| 4 — Platform Hardening | Source change detection, backfill automation, DR, cost optimization |

## Contributing

- Follow Conventional Commits: `type(scope): description`
- Branch per task from `main`; PR with review required before merge
- No secrets in code, logs, or documentation (AGENTS.md §6.1)
- Run pre-commit hooks before committing
- All CI checks must pass before merge
- See `AGENTS.md` for the full agent operating contract

## License

Private — KLIBRA Data Platform Team
