"""Severity-based alert router — PRD §32.3, TDD §30."""

from __future__ import annotations

import logging
from dataclasses import dataclass

__all__ = ["AlertRecord", "route_alert"]

logger = logging.getLogger(__name__)

# Severity levels mirror PRD §32.3
SEVERITY_MAP: dict[str, list[str]] = {
    "P0": ["technical_owner", "data_owner", "business_owner"],
    "P1": ["technical_owner", "data_owner", "business_owner"],
    "P2": ["technical_owner", "data_owner"],
    "P3": ["technical_owner"],
}

SLO_RETRY: dict[str, str] = {
    "P0": "immediate",
    "P1": "within 4h",
    "P2": "within 4h",
    "P3": "within 24h",
}


@dataclass(frozen=True, slots=True)
class AlertRecord:
    run_id: str
    pipeline_id: str
    dataset_id: str
    severity: str
    summary: str | None = None

    def targets(self) -> list[str]:
        return SEVERITY_MAP.get(self.severity, [])


def route_alert(record: AlertRecord) -> list[str]:
    """Route an alert to responsible owners based on severity.

    Returns the list of recipient roles for this severity.
    """
    targets = record.targets()
    logger.info(
        "Alert [%s] for %s/%s routed to %s",
        record.severity,
        record.dataset_id,
        record.run_id,
        targets,
    )
    return targets
