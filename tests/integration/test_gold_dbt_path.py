"""Integration: Gold dbt path non-zero exit (T017, FR-003)."""

from __future__ import annotations

import subprocess

import pytest

from orchestration.tasks import build_gold


def test_gold_dbt_nonzero_raises(monkeypatch) -> None:
    class FakeCompletedProcess:
        returncode = 1
        stderr = "dbt: no such model"
        stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: FakeCompletedProcess())
    with pytest.raises(RuntimeError, match="dbt build failed"):
        build_gold({"products": {}})  # not legacy guard -> triggers dbt path
