"""Storage factory — env-driven MinIO/boto3 selection.

TDD §6, ADR-001. Single primary driver key: ``KLIBRA_ENV``.
``development`` -> MinIO via boto3 with ``endpoint_url``; otherwise boto3
against AWS S3. Both paths return a :class:`boto3.client.S3` so downstream
code (raw + quarantine writers) uses one keyword-only ``put_object`` form.
"""

from __future__ import annotations

import os
from typing import Any

from ingestion.storage.raw import (
    CloudStorageWriter,
    LocalStorageWriter,
    RawStorageWriter,
)

__all__ = [
    "make_storage_writer",
    "make_storage_client",
    "is_development",
]


def is_development(env: str | None = None) -> bool:
    """Return True when ``KLIBRA_ENV`` is ``development``.

    Args:
        env: Override value; defaults to ``os.environ["KLIBRA_ENV"]``.
    """
    value = env if env is not None else os.environ.get("KLIBRA_ENV", "")
    return value.strip().lower() == "development"


def make_storage_writer() -> RawStorageWriter:
    """Build a :class:`RawStorageWriter` for the current environment.

    Raises ``RuntimeError`` when required env vars are missing or bucket name
    cannot be resolved (fail-fast per FR-002).
    """
    bucket = _pick_raw_bucket()
    if is_development():
        endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
        access = os.environ.get("MINIO_ACCESS_KEY", "")
        secret = os.environ.get("MINIO_SECRET_KEY", "")
        if not access or not secret:
            raise RuntimeError(
                "MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when KLIBRA_ENV=development"
            )
        return LocalStorageWriter(
            bucket_name=bucket,
            endpoint_url=endpoint,
            access_key=access,
            secret_key=secret,
        )
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    return CloudStorageWriter(bucket_name=bucket, region=region)


def make_storage_client() -> Any:
    """Build the underlying object-storage client for the current environment.

    Unified to :class:`boto3.client.S3` for both dev and prod (ADR-006,
    Constitution IX). In development the local MinIO endpoint is passed via
    ``endpoint_url``; credentials come from ``MINIO_*`` env vars. In
    production ``AWS_*`` env vars (or instance role) are used.
    """
    import boto3

    if is_development():
        endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
        access = os.environ.get("MINIO_ACCESS_KEY", "")
        secret = os.environ.get("MINIO_SECRET_KEY", "")
        if not access or not secret:
            raise RuntimeError(
                "MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when KLIBRA_ENV=development"
            )
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name=os.environ.get("AWS_REGION", "ap-southeast-1"),
        )
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))


def _pick_raw_bucket() -> str:
    """Resolve the raw bucket name from env vars.

    Prefer the explicit ``KLIBRA_RAW_BUCKET`` override; fall back to
    ``AWS_S3_BUCKET_RAW`` (existing convention) and finally to a sensible
    default that matches ``infrastructure/terraform/main.tf``.
    """
    return (
        os.environ.get("KLIBRA_RAW_BUCKET")
        or os.environ.get("AWS_S3_BUCKET_RAW")
        or "klibra-data-raw"
    )
