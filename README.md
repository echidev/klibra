# FINDEX — Financial Data & Intelligence Exchange

FINDEX is an enterprise financial data platform for Indonesia's financial ecosystem.

## Features

- Ingest financial data from BI, OJK, and BPS
- Standardize into canonical observation model (`fact_financial_observation`)
- Lakehouse architecture (Raw → Bronze → Silver → Gold → Quarantine)
- Automated quality controls and quarantine for blocking failures
- Gold data products: `gold_credit_growth`, `gold_financial_sector_monitor`, `gold_macro_financial_context`, `gold_regional_financial_profile`
- Full lineage from Gold → Silver → Bronze → Raw → Source
- Structured logging, ISO 25010-compliant code, enterprise standards

## Quick Start

```bash
# Clone
git clone <repo-url>
cd findex

# Install dependencies
pip install -r requirements.txt

# Start local dev environment
docker compose up -d

# Run Airflow
airflow db init
airflow webserver &
airflow scheduler &
```

## Project Structure

```text
src/            # Python source (connectors, pipelines, utils)
dags/           # Airflow DAGs (ingestion, transformation, quality)
models/         # dbt models (staging, silver, gold)
infra/          # Terraform IaC (AWS resources, IAM, Secrets Manager)
docs/           # Architecture, ADRs, governance, runbooks
tests/          # Unit, contract, integration, quality tests
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- Source API keys (BI, OJK, BPS)
- AWS credentials (if using AWS directly)
- PostgreSQL settings
- Airflow settings
- MinIO settings

**Never commit `.env` to version control.**

## Contributing

- Follow Conventional Commits: `type(scope): description`
- No secrets in code, logs, or documentation
- Run pre-commit hooks before committing
- All CI checks must pass before merge
- Code review required before merge

## License

Private — FINDEX Team

---

*Built with ❤️ for Indonesia's financial data ecosystem.*
