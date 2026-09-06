"""Test that discover_datasets wires CoinGecko and keeps IMF deferred (T040/T041)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from orchestration.tasks import discover_datasets


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
