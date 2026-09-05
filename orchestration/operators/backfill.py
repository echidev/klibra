"""Backfill operator — TDD §17.

.. deprecated::
    Use :mod:`orchestration.operators.backfill_orchestrator` instead.
    This module re-exports the canonical :class:`BackfillRequest`.
"""

from __future__ import annotations

from orchestration.operators.backfill_orchestrator import (  # noqa: F401
    BackfillOrchestrator as _Orchestrator,
)
from orchestration.operators.backfill_orchestrator import (
    BackfillRequest,
)
from orchestration.operators.backfill_orchestrator import (
    BackfillStatus as ValidationStatus,
)

__all__ = ["BackfillRequest", "ValidationStatus", "validate_backfill"]


def validate_backfill(req: BackfillRequest) -> tuple[bool, list[str]]:  # noqa: F811
    """Compat wrapper delegating to :class:`BackfillOrchestrator` validation."""

    from orchestration.operators.backfill_orchestrator import _validate

    errors = _validate(req)
    return (len(errors) == 0, errors)
