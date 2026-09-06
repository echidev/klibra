"""Integration: discovery wiring (T041/T042)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from orchestration.tasks import discover_datasets


def _catalog(tmp: Path) -> Path:
    p = tmp / "catalog.yaml"
    p.write_text(
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
    return p


def test_discovery_imf_deferred(tmp_path, caplog) -> None:
    caplog.set_level(logging.WARNING)
    out = discover_datasets(_catalog(tmp_path))
    sources = {d["source_id"] for d in out["datasets"]}
    assert "imf" not in sources
    assert any("IMF" in r.message for r in caplog.records)
