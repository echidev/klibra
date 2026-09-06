"""Storage factory — env-driven MinIO/boto3 selection.

TDD §6, ADR-001. Single primary driver key: ``KLIBRA_ENV``.
``development`` -> MinIO via ``MINIO_*``; otherwise boto3 via ``AWS_*``.
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

    Mirrors :func:`make_storage_writer` so the DAG can pass the same client
    into both the raw writer and the quarantine writer.
    """
    if is_development():
        from minio import Minio

        endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
        access = os.environ.get("MINIO_ACCESS_KEY", "")
        secret = os.environ.get("MINIO_SECRET_KEY", "")
        if not access or not secret:
            raise RuntimeError(
                "MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when KLIBRA_ENV=development"
            )
        secure = endpoint.startswith("https")
        return Minio(
            endpoint.replace("http://", "").replace("https://", ""),
            access_key=access,
            secret_key=secret,
            secure=secure,
        )
    import boto3

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
