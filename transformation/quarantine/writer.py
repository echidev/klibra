"""Quarantine writer — TDD §23, PRD §13.

Records that fail a blocking quality check (P0/P1) are routed to the
quarantine layer instead of being promoted to Silver/Gold. This module
captures the failure context so investigators can reproduce and resolve.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
from dataclasses import asdict, dataclass
from typing import Any

__all__ = ["QuarantineRecord", "write_quarantine"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    run_id: str
    dataset_id: str
    failure_rule: str
    failed_value: Any | None = None
    timestamp: str = ""
    error_details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # default to now if not provided (frozen so we use object.__setattr__)
        if not self.timestamp:
            object.__setattr__(
                self,
                "timestamp",
                dt.datetime.now(dt.UTC).isoformat(),
            )


def write_quarantine(
    record: QuarantineRecord,
    *,
    base_path: str = "/tmp/klibra-quarantine",
) -> str:
    """Persist a quarantine record to disk and return its file path."""
    target_dir = pathlib.Path(base_path) / record.dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{record.run_id}-{record.failure_rule}.json"
    fpath = target_dir / fname
    fpath.write_text(json.dumps(asdict(record), indent=2, default=str))
    logger.warning(
        "quarantine: dataset=%s run=%s rule=%s",
        record.dataset_id,
        record.run_id,
        record.failure_rule,
    )
    return str(fpath)
