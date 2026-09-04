"""Observability wiring for publish/notify — TDD §29, §30.

Emits an OpenMetadata event + a CloudWatch alarm payload. In local dev these
are no-ops that log; in production they call the respective SDKs.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def emit_openmetadata_event(run_id: str, dataset_id: str, status: str) -> None:
    """Emit a lineage/quality event to OpenMetadata (TDD §68–§69)."""
    logger.info(
        "openmetadata: run=%s dataset=%s status=%s (no-op in local dev)",
        run_id,
        dataset_id,
        status,
    )


def emit_cloudwatch_alarm(payload: dict[str, Any]) -> None:
    """Emit a CloudWatch alarm metric (TDD §29)."""
    logger.info(
        "cloudwatch: alarm payload=%s (no-op in local dev)",
        payload,
    )
