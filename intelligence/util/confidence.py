"""Intelligence publish gate — coverage + confidence helpers (003, FR-18, gap G11).

Implements the ``coverage_ratio`` and ``confidence`` helpers that the
publish gate (`coverage_ratio >= min_required_inputs`) delegates to.

Coverage
    coverage_ratio = len(present ∩ expected) / len(expected)

    where *present* is the set of ``weights`` keys whose ``inputs``
    value is not ``None``.

Confidence
    confidence = min(1.0, coverage / declared_min)

So the gate threshold is a declared minimum coverage; the reported
confidence is the coverage rescaled by that minimum.

References: plan Decision 7 / FR-17, FR-18 / SC-D-4.
"""

from __future__ import annotations

__all__ = ["confidence", "coverage_ratio"]


def coverage_ratio(
    inputs: dict[str, float | None],
    weights: dict[str, float],
) -> float:
    """Return the coverage ratio for a (inputs, weights) pair.

    Parameters
    ----------
    inputs:
        Dict of ``{metric_id: value}`` for the current scoring period.
        ``None`` values are treated as absent.
    weights:
        Dict of ``{metric_id: weight}`` declaring the scorer's expected
        components.

    Returns
    -------
    ``float`` in ``[0, 1]``; ``1.0`` when every expected input is present
    with a non-``None`` value, ``0.0`` when none.
    """

    if not weights:
        return 1.0
    expected = set(weights.keys())
    present = {k for k in expected if inputs.get(k) is not None}
    return len(present) / len(expected)


def confidence(coverage: float, declared_min: float = 0.5) -> float:
    """Return a capped confidence score rescaled by ``declared_min``.

    Parameters
    ----------
    coverage:
        The ``coverage_ratio`` for the current run.
    declared_min:
        The per-product ``min_required_inputs`` threshold (default ``0.5``).

    Returns
    -------
    ``float`` in ``[0, 1]``; capped at ``1.0``.
    """

    if declared_min <= 0:
        return 1.0
    return min(1.0, coverage / declared_min)
