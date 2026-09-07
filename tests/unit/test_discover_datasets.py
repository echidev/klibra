"""Test that discover_datasets wires CoinGecko and keeps IMF deferred (T040/T041)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
import yaml

from orchestration.tasks import _resolve_catalog_path, discover_datasets


def _catalog(tmp: Path) -> Path:
    catalog = tmp / "catalog.yaml"
    catalog.write_text(
        yaml.safe_dump(
            {
                "sources": {
                    "worldbank": {"live_request_verified": True},
                    "ecb": {"live_request_verified": True},
                    "fred": {"live_request_verified": True},
                    "alphavantage": {"live_request_verified": True},
                    "coingecko": {"live_request_verified": True},
                    "imf": {"live_request_verified": True},
                }
            }
        )
    )
    return catalog


def test_discover_datasets_includes_coingecko(tmp_path: Path, caplog) -> None:
    caplog.set_level(logging.WARNING, logger="klibra-orchestration")
    out = discover_datasets(_catalog(tmp_path))
    sources = {d["source_id"] for d in out["datasets"]}
    assert "coingecko" in sources
    assert "imf" not in sources  # deferred
    assert any("IMF" in r.message or "imf" in r.message.lower() for r in caplog.records)


def test_resolve_catalog_path_defaults_to_repo_root() -> None:
    """_resolve_catalog_path(None) resolves to <repo_root>/docs/data/source_catalog.yaml."""
    # tasks.py lives at <repo>/orchestration/tasks.py → parents[1] = repo root.
    # This test file lives at <repo>/tests/unit/test_discover_datasets.py → parents[2] = repo root.
    p = _resolve_catalog_path(None)
    expected = Path(__file__).resolve().parents[2] / "docs" / "data" / "source_catalog.yaml"
    assert p == expected


def test_resolve_catalog_path_passed_through(tmp_path: Path) -> None:
    c = tmp_path / "catalog.yaml"
    c.write_text("sources: {}")
    assert _resolve_catalog_path(c) == c
    assert _resolve_catalog_path(str(c)) == c


def test_discover_datasets_cwd_independent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cwd = tmp_path / "somewhere"
    fake_cwd.mkdir(exist_ok=True)
    monkeypatch.chdir(fake_cwd)
    out = discover_datasets(_catalog(tmp_path))
    assert any(d["source_id"] == "worldbank" for d in out["datasets"])
