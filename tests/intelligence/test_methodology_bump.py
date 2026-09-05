"""Methodology bump tests — FR-8 002-D.

Verify that weight changes without a MAJOR methodology bump raise
``MethodologyVersionBumpRequired``.
"""

from __future__ import annotations

import pytest

from intelligence.composite import (
    CompositeScorer,
    MethodologyVersionBumpRequired,
)
from intelligence.util.version_pin import check_weights_pinned, pin_weights


class _StubScorer(CompositeScorer):
    product_id: str = "intelligence_stub"
    methodology_version: str = "1.0.0"
    weights: dict[str, float] = {"a": 0.5, "b": 0.5}

    def normalize(self, inputs):
        return dict(inputs)

    def aggregate(self, components):
        return 0.0


def test_pin_weights_returns_version_and_hash() -> None:
    version, hash_ = pin_weights({"a": 0.5, "b": 0.5}, "1.0.0")
    assert version == "1.0.0"
    assert len(hash_) == 64  # sha256


def test_check_weights_pinned_no_change_passes() -> None:
    weights = {"a": 0.5, "b": 0.5}
    _, hash_ = pin_weights(weights, "1.0.0")
    # Same weights — no change — should not raise
    check_weights_pinned(weights, "1.0.0", hash_)


def test_check_weights_pinned_change_raises() -> None:
    weights = {"a": 0.5, "b": 0.5}
    _, hash_ = pin_weights(weights, "1.0.0")
    modified = {"a": 0.7, "b": 0.3}
    with pytest.raises(MethodologyVersionBumpRequired):
        check_weights_pinned(modified, "1.0.0", hash_)


def test_pin_weights_rejects_non_semver() -> None:
    with pytest.raises(ValueError, match="semver"):
        pin_weights({"a": 0.5}, "1.0")  # missing patch
