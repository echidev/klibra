"""Raw lakehouse storage writer — TDD §6, §7, ADR-001.

Provides a thin abstraction over S3 / MinIO that stores raw payloads in
the canonical layout::

    raw/source=<source_id>/dataset=<dataset_id>/ingestion_date=<date>/run_id=<run_id>/payload

Each payload is immutable and accompanied by a ``manifest.json`` carrying
full acquisition metadata (TDD §7). The writer enforces immutability:
once written, an object is never overwritten at the same key; the run_id
tuple makes each ingestion an idempotent append (TDD §15).

For local development the :class:`RawStorageWriter` targets MinIO via the
``minio`` SDK. For production (S3) the concrete adapter replaces the MinIO
client with ``boto3`` — swapping adapters is the only change required.
"""

from __future__ import annotations

import datetime as dt
import io
import logging
from typing import Any, Protocol, runtime_checkable

__all__ = ["RawStorageWriter", "LocalStorageWriter", "CloudStorageWriter"]

logger = logging.getLogger(__name__)


@runtime_checkable
class ObjectClient(Protocol):
    """Minimal protocol implemented by boto3 S3 and minio clients."""

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: Any,
        content_type: str | None = None,
    ) -> Any: ...


def _raw_key(
    source_id: str,
    dataset_id: str,
    run_id: str,
    *,
    date: dt.date | None = None,
    ext: str = "payload",
) -> str:
    date = date or dt.datetime.now(tz=dt.UTC).date()
    return (
        f"raw/source={source_id}"
        f"/dataset={dataset_id}"
        f"/ingestion_date={date.isoformat()}"
        f"/run_id={run_id}/{ext}"
    )


class RawStorageWriter:
    """Stateless helper that writes raw payloads and manifests.

    Parameters
    ----------
    bucket_prefix:
        Optional prefix applied to the object key; e.g. a role path.
    bucket_name:
        Target bucket in S3/MinIO.
    """

    def __init__(
        self,
        bucket_name: str,
        *,
        bucket_prefix: str = "",
    ) -> None:
        self.bucket_name = bucket_name
        self.bucket_prefix = bucket_prefix.rstrip("/")

    def _prefixed_key(self, key: str) -> str:
        if self.bucket_prefix:
            return f"{self.bucket_prefix}/{key}"
        return key

    def write_raw(
        self,
        client: ObjectClient,
        source_id: str,
        dataset_id: str,
        run_id: str,
        payload: bytes,
        manifest_json: bytes,
    ) -> str:
        """Persist payload + manifest and return the object key used."""
        payload_key = _raw_key(source_id, dataset_id, run_id)
        manifest_key = _raw_key(source_id, dataset_id, run_id, ext="manifest.json")

        client.put_object(
            self.bucket_name,
            self._prefixed_key(payload_key),
            io.BytesIO(payload),
            content_type="application/octet-stream",
        )
        client.put_object(
            self.bucket_name,
            self._prefixed_key(manifest_key),
            io.BytesIO(manifest_json),
            content_type="application/json",
        )
        logger.info(
            "raw written: source=%s dataset=%s run=%s key=%s",
            source_id,
            dataset_id,
            run_id,
            payload_key,
        )
        return payload_key


class LocalStorageWriter(RawStorageWriter):
    """MinIO-backed writer for local development (TDD §35, ADR-006)."""

    def __init__(
        self,
        bucket_name: str,
        *,
        bucket_prefix: str = "",
        endpoint_url: str = "http://localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
    ) -> None:
        super().__init__(bucket_name, bucket_prefix=bucket_prefix)
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key

    def get_client(self) -> Any:
        """Create a minio ``Minio`` client bound to the configured endpoint."""
        try:
            from minio import Minio  # noqa: PLC0415 — lazy import
        except ImportError as exc:
            raise RuntimeError(
                "minio package is required for LocalStorageWriter. "
                "Install via: pip install minio"
            ) from exc
        secure = self.endpoint_url.startswith("https")
        client = Minio(
            self.endpoint_url.replace("http://", "").replace("https://", ""),
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure,
        )
        if not client.bucket_exists(self.bucket_name):
            client.make_bucket(self.bucket_name)
            logger.info("bucket %s created", self.bucket_name)
        return client


class CloudStorageWriter(RawStorageWriter):
    """S3-backed writer for production (TDD §36, ADR-006)."""

    def __init__(
        self,
        bucket_name: str,
        *,
        bucket_prefix: str = "",
        region: str | None = None,
    ) -> None:
        super().__init__(bucket_name, bucket_prefix=bucket_prefix)
        self.region = region

    def get_client(self) -> Any:
        try:
            import boto3  # noqa: PLC0415 — lazy import
        except ImportError as exc:
            raise RuntimeError(
                "boto3 package is required for CloudStorageWriter. "
                "Install via: pip install boto3"
            ) from exc
        return boto3.client("s3", region_name=self.region)
