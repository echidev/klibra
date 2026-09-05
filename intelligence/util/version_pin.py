"""Methodology version pin — FR-8 002-D, Constitution §V.

Ensures that intelligence product weights are bound to a methodology
version. Weight changes without a MAJOR bump raise
``MethodologyVersionBumpRequired``.
"""

from __future__ import annotations

import hashlib
import json
import re

from intelligence.composite import MethodologyVersionBumpRequired

__all__ = ["check_weights_pinned", "pin_weights"]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _hash_weights(weights: dict[str, float]) -> str:
    payload = json.dumps(weights, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def pin_weights(
    weights: dict[str, float],
    methodology_version: str,
) -> tuple[str, str]:
    """Pin ``weights`` to ``methodology_version`` and return (version, hash)."""

    if not SEMVER_RE.match(methodology_version):
        raise ValueError(f"methodology_version must be semver X.Y.Z, got {methodology_version!r}")
    return (methodology_version, _hash_weights(weights))


def check_weights_pinned(
    weights: dict[str, float],
    expected_methodology_version: str,
    stored_hash: str,
) -> None:
    """Raise if weights differ from the pinned methodology hash."""

    if _hash_weights(weights) != stored_hash:
        raise MethodologyVersionBumpRequired(
            "Weights changed without MAJOR methodology bump",
            expected_version=expected_methodology_version,
        )
