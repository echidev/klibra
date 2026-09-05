"""Metric semver helpers — FR-4 002-C.

Implements the metric semver policy for ``semantic/catalog.py``:

  - MAJOR bump for formula/meaning change requires governance approval.
  - MINOR bump backward-compatible dimension or metadata addition.
  - PATCH bump documentation or non-semantic implementation fix.

Re-exported from ``semantic/catalog.py``; this module provides the
standalone helpers that the semantic metric contracts reference.
"""

from __future__ import annotations

import re

__all__ = ["GovernanceApprovalRequired", "validate_semver_transition"]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _parse_semver(version: str) -> tuple[int, int, int]:
    if not SEMVER_RE.match(version):
        raise ValueError(f"version must be semver X.Y.Z, got {version!r}")
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


class GovernanceApprovalRequired(RuntimeError):  # noqa: N818
    """Raised when a MAJOR version bump is requested without governance approval."""

    def __init__(self, message: str, *, metric_id: str | None = None) -> None:
        super().__init__(message)
        self.metric_id = metric_id


def validate_semver_transition(
    old_version: str, new_version: str, *, metric_id: str | None = None
) -> None:
    """Validate that a metric version bump follows governance policy.

    MAJOR bump without ``governance_approved=True`` raises
    ``GovernanceApprovalRequired``. MINOR and PATCH are allowed without
    approval.

    Parameters
    ----------
    old_version:
        Previous metric version.
    new_version:
        New metric version to validate.
    metric_id:
        Optional metric identifier for the error message.
    """
    old = _parse_semver(old_version)
    new = _parse_semver(new_version)
    if new[0] > old[0]:
        raise GovernanceApprovalRequired(
            f"MAJOR version bump for metric {metric_id!r} requires governance approval ({old_version} -> {new_version})",
            metric_id=metric_id,
        )
