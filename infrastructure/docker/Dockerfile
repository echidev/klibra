# Dockerfile — KLIBRA ingestion + transformation runtime
# Aligned with TDD §35, plan.md § Compute Topology.
#
# Build:
#   docker build -t klibra-runtime:latest -f infrastructure/docker/Dockerfile .
#
# Run (example for a connector):
#   docker run --rm -e KLIBRA_ENV=development klibra-runtime:latest \
#     python -m ingestion.connectors.worldbank --dataset NY.GDP.MKTP.CD

FROM python:3.11-slim AS base

# Pinned versions track requirements.txt exactly
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/klibra

# System dependencies: lxml needs libxml2/libxslt (TDD §13.1 sources).
# dbt-duckdb ships its own DuckDB wheel; no extra C libs required.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies — pinned
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Application source
COPY ingestion/ ./ingestion/
COPY transformation/ ./transformation/
COPY semantic/ ./semantic/
COPY intelligence/ ./intelligence/
COPY orchestration/ ./orchestration/
COPY pyproject.toml ./

# Non-root runtime
RUN useradd --system --create-home --shell /bin/bash klibra && \
    chown -R klibra:klibra /opt/klibra
USER klibra

# Default entrypoint is overridable per workload
ENTRYPOINT ["python", "-m"]
CMD ["ingestion.cli"]
