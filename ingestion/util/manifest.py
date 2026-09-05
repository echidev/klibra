"""Manifest writer for raw lakehouse objects — TDD §7, ADR-001.

Every raw payload is accompanied by a JSON manifest that preserves the full
acquisition context (TDD §7 raw object convention, ADR-002 emit_metadata).
The manifest SHA256 is propagated to Silver (``payload_hash``) for
idempotency checks and lineage.

Example call::

    from ingestion.util.manifest import sha256_hex, build_manifest

    content_hash = sha256_hex(payload)
    manifest = build_manifest(
        source_id="worldbank",
        dataset_id="NY.GDP.MKTP.CD",
        run_id=run_id,
        source_url=url,
        content_hash=content_hash,
    )
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

__all__ = [
    "build_manifest",
    "manifest_to_json",
    "sha256_hex",
]


def sha256_hex(payload: bytes | str) -> str:
    """Return hex SHA256 of ``payload``."""

    if isinstance(payload, str):
        payload = payload.encode()
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    *,
    source_id: str,
    dataset_id: str,
    run_id: str,
    source_url: str,
    content_hash: str,
    payload_format: str = "json",
    request_params: dict[str, Any] | None = None,
    response_metadata: dict[str, Any] | None = None,
    source_publication_timestamp: dt.datetime | None = None,
    source_version: str | None = None,
    retrieved_at: dt.datetime | None = None,
    connector_version: str = "0.0.0",
    schema_version: str = "v1",
) -> dict[str, Any]:
    """Build the normalized manifest dict written alongside a raw payload."""

    rt = retrieved_at or dt.datetime.now(tz=dt.UTC)
    return {
        "source_id": source_id,
        "dataset_id": dataset_id,
        "retrieval_timestamp": rt.isoformat(),
        "source_url": source_url,
        "request_params": dict(request_params or {}),
        "response_metadata": dict(response_metadata or {}),
        "content_hash": content_hash,
        "payload_format": payload_format,
        "run_id": run_id,
        "connector_version": connector_version,
        "source_publication_timestamp": (
            source_publication_timestamp.isoformat()
            if source_publication_timestamp is not None
            else None
        ),
        "source_version": source_version,
        "schema_version": schema_version,
    }


def manifest_to_json(manifest: dict[str, Any], *, indent: int = 2) -> str:
    """Pretty-serialize a manifest without trailing whitespace drift."""

    return json.dumps(manifest, indent=indent, sort_keys=True) + "\n"
