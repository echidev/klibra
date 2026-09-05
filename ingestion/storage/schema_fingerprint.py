"""Source payload schema fingerprinting — TDD §19, §74, PRD FR-F-1.

Persists a fingerprint of the flattened payload keys/types per run and
classifies changes as compatible / potentially breaking / breaking.
This module is used by the platform to detect and surface schema drift
before downstream promotion, satisfying R4 advanced source-change detection.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

__all__ = [
    "ChangeClass",
    "SchemaFingerprint",
    "classify_schema_change",
    "fingerprint_payload",
]

ChangeClass = Literal["COMPATIBLE", "POTENTIALLY_BREAKING", "BREAKING"]


def _flatten(obj: Any, prefix: str = "", out: dict[str, str] | None = None) -> dict[str, str]:
    """Flatten a nested JSON-like payload into a ``field -> type`` map."""

    if out is None:
        out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            _flatten(v, key, out)
    elif isinstance(obj, list):
        # Represent list as "array:<elem_type>" for the first element
        elem = obj[0] if obj else None
        out[prefix] = f"array:{type(elem).__name__}" if elem is not None else "array"
    else:
        out[prefix] = type(obj).__name__
    return out


def fingerprint_payload(payload: bytes) -> dict[str, str]:
    """Return a flattened ``field -> type`` map for a raw payload."""

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        # Non-JSON payload (e.g. CSV / unknown): fingerprint as opaque type
        return {"__opaque__": "bytes"}
    return _flatten(data)


def _schema_hash(schema: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SchemaFingerprint:
    """Persisted schema fingerprint with change classification."""

    source_id: str
    dataset_id: str
    run_id: str
    schemas: dict[str, str]
    hash: str
    change_class: ChangeClass
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", dt.datetime.now(dt.UTC).isoformat())


def classify_schema_change(
    old: dict[str, str],
    new: dict[str, str],
) -> ChangeClass:
    """Classify a schema change per TDD §19 / §74.

    Compatible: only added nullable fields / metadata.
    Potentially breaking: changed type or added required field.
    Breaking: removed field or structural incompatibility.
    """
    removed = set(old) - set(new)
    added = set(new) - set(old)
    changed_type = {k for k in set(old) & set(new) if old[k] != new[k]}
    if removed:
        return "BREAKING"
    if changed_type:
        return "POTENTIALLY_BREAKING"
    if added:
        return "POTENTIALLY_BREAKING"
    return "COMPATIBLE"


class SchemaFingerprintStore:
    """In-memory persistence of fingerprints per source dataset.

    In production this is backed by the ``schema_fingerprint`` table from
    ``V001__control_plane.sql``. The API is identical.
    """

    def __init__(self) -> None:
        self._latest: dict[tuple[str, str], SchemaFingerprint] = {}

    def record(
        self,
        *,
        source_id: str,
        dataset_id: str,
        run_id: str,
        payload: bytes,
    ) -> SchemaFingerprint:
        """Record a fingerprint and classify change vs the last run."""

        new_schema = fingerprint_payload(payload)
        new_hash = _schema_hash(new_schema)
        key = (source_id, dataset_id)
        old = self._latest.get(key)
        if old is None:
            change_class: ChangeClass = "COMPATIBLE"  # first run
        else:
            change_class = classify_schema_change(old.schemas, new_schema)
        fp = SchemaFingerprint(
            source_id=source_id,
            dataset_id=dataset_id,
            run_id=run_id,
            schemas=new_schema,
            hash=new_hash,
            change_class=change_class,
        )
        self._latest[key] = fp
        return fp

    def latest(self, source_id: str, dataset_id: str) -> SchemaFingerprint | None:
        return self._latest.get((source_id, dataset_id))
