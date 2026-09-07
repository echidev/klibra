"""Quarantine storage writer — TDD §6/§7, contracts/quarantine.md.

Persists bad records to a quarantine layer with a manifest describing the
reason. Failures are logged at WARN and swallowed so the main pipeline
continues (per `contracts/quarantine.md` Failure Isolation).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
from typing import Any, Protocol, runtime_checkable

from ingestion.storage.raw import ObjectClient, _put_object, _put_object

__all__ = [
    "QuarantineStorageWriter",
    "build_quarantine_manifest",
    "quarantine_key",
]

logger = logging.getLogger(__name__)


@runtime_checkable
class QuarantineObjectClient(ObjectClient, Protocol):
    """Marker protocol — same shape as :class:`ingestion.storage.raw.ObjectClient`."""


def quarantine_key(
    source_id: str,
    dataset_id: str,
    run_id: str,
    observation_id: str,
) -> str:
    """Return the canonical quarantine object key.

    Layout: ``quarantine/source={source_id}/dataset={dataset_id}/run_id={run_id}/{observation_id}.json``
    """
    return (
        f"quarantine/source={source_id}"
        f"/dataset={dataset_id}"
        f"/run_id={run_id}"
        f"/{observation_id}.json"
    )


def build_quarantine_manifest(
    record: dict[str, Any],
    reason: str,
    *,
    observation_id: str = "",
    run_id: str = "",
    source_id: str = "",
    dataset_id: str = "",
    timestamp: dt.datetime | None = None,
) -> dict[str, Any]:
    """Build a quarantine manifest per `data-model.md` QuarantineManifest."""
    return {
        "source_id": source_id or record.get("source_id", ""),
        "dataset_id": dataset_id or record.get("dataset_id", ""),
        "run_id": run_id or record.get("run_id", ""),
        "observation_id": observation_id or record.get("observation_id", ""),
        "quarantine_reason": reason,
        "quality_status": "QUARANTINED",
        "original_record": record,
        "quarantine_timestamp": (timestamp or dt.datetime.now(tz=dt.UTC)).isoformat(),
    }


class QuarantineStorageWriter:
    """Stateless writer that persists quarantined records.

    Re-uses the same :class:`ObjectClient` protocol as the raw writer so it
    can share a MinIO/boto3 client with the rest of the pipeline.
    """

    def __init__(self, bucket_name: str, *, bucket_prefix: str = "") -> None:
        self.bucket_name = bucket_name
        self.bucket_prefix = bucket_prefix.rstrip("/")

    def _prefixed_key(self, key: str) -> str:
        if self.bucket_prefix:
            return f"{self.bucket_prefix}/{key}"
        return key

    def write_quarantine(
        self,
        client: QuarantineObjectClient,
        source_id: str,
        dataset_id: str,
        run_id: str,
        record: dict[str, Any],
        reason: str,
        *,
        observation_id: str = "",
    ) -> str:
        """Write a quarantine manifest to the configured bucket.

        Returns the object key. Errors are caught and logged at WARN
        so the main pipeline is never broken by quarantine failures.
        """
        manifest = build_quarantine_manifest(
            record,
            reason,
            observation_id=observation_id,
            run_id=run_id,
            source_id=source_id,
            dataset_id=dataset_id,
        )
        observation = manifest["observation_id"] or "unknown"
        key = self._prefixed_key(quarantine_key(source_id, dataset_id, run_id, observation))
        try:
            _put_object(
                client,
                self.bucket_name,
                key,
                io.BytesIO(json.dumps(manifest).encode("utf-8")),
                content_type="application/json",
            )
        except Exception as exc:  # noqa: BLE001 — quarantine must not break the pipeline
            logger.warning(
                "quarantine write failed source_id=%s dataset_id=%s run_id=%s error=%s",
                source_id,
                dataset_id,
                run_id,
                exc,
            )
            return ""
        return key
