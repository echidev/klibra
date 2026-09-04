"""Idempotency key generator — TDD §71, Constitution XII.

Pipeline reruns for the same source snapshot must not create duplicate
facts. KLIBRA implements a deterministic key spec (TDD §71, ADR-007):

    hash(source_id, dataset_id, source_period, source_version, payload_hash)

The formula is deliberately small, cryptographically strong, and stable
across deployments. Callers combine upstream identifiers; connectors pass
payload_hash from ``manifest.sha256_hex``.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
    "compute_idempotency_key",
    "validate_idempotency_components",
]

COMPONENT_RE = re.compile(r"^[A-Za-z0-9_.:/-]*$")


def _encode_components(components: list[str]) -> str:
    return "\x1f".join(components)


def compute_idempotency_key(
    source_id: str,
    dataset_id: str,
    source_period: str,
    source_version: str | None,
    payload_hash: str,
) -> str:
    """Return a deterministic 64-char hex key for a source snapshot."""

    components = [
        source_id,
        dataset_id,
        source_period,
        source_version or "",
        payload_hash,
    ]

    for c in components:
        if not isinstance(c, str):
            msg = f"component must be str, got {type(c).__name__!r}"
            raise TypeError(msg)
    encoded = _encode_components(components)
    return hashlib.sha256(encoded.encode()).hexdigest()


def validate_idempotency_components(
    source_id: str,
    dataset_id: str,
    source_period: str,
    source_version: str | None,
    payload_hash: str,
) -> list[str]:
    """Validate that components are non-empty strings and syntactically sane.

    Returns a list of validation error messages (empty on success).
    """

    errors: list[str] = []
    if not source_id:
        errors.append("source_id is required")
    if not dataset_id:
        errors.append("dataset_id is required")
    if not source_period:
        errors.append("source_period is required")
    if not payload_hash:
        errors.append("payload_hash is required")
    for label, value in [
        ("source_id", source_id),
        ("dataset_id", dataset_id),
        ("source_period", source_period),
        ("source_version", source_version or ""),
        ("payload_hash", payload_hash),
    ]:
        if value and not COMPONENT_RE.match(value):
            errors.append(f"{label} contains disallowed characters: {value!r}")
    return errors
