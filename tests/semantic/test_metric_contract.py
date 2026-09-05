"""Validate that every entry in docs/data/contracts/semantic/ matches the metric contract.

FR-10 002-C requires contract tests. These tests run in CI per
`.github/workflows/ci.yml` (001 T044).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

SCHEMA = json.loads(
    pathlib.Path(
        "specs/002-release-2-multi-source/contracts/metric-contract.schema.json"
    ).read_text()
)


def _validate(obj: Any) -> list[str]:
    """Tiny validator (avoid jsonschema dep here to keep tests pure-python)."""

    errors: list[str] = []
    if not isinstance(obj, dict):
        return [f"object is not a dict, got {type(obj).__name__}"]
    for required in SCHEMA.get("required", []):
        if required not in obj:
            errors.append(f"missing required field: {required!r}")
    metric_id_pattern = SCHEMA["properties"]["metric_id"]["pattern"]
    import re

    metric_id_re = re.compile(metric_id_pattern)
    if "metric_id" in obj and not metric_id_re.match(str(obj["metric_id"])):
        errors.append(f"metric_id {obj['metric_id']!r} does not match {metric_id_pattern}")
    version_re = re.compile(SCHEMA["properties"]["version"]["pattern"])
    if "version" in obj and not version_re.match(str(obj["version"])):
        errors.append(f"version {obj['version']!r} must be semver X.Y.Z")
    enum = SCHEMA["properties"]["aggregation_policy"]["enum"]
    if "aggregation_policy" in obj and obj["aggregation_policy"] not in enum:
        errors.append(f"aggregation_policy {obj['aggregation_policy']!r} not in {enum}")
    return errors


@pytest.mark.parametrize(
    "path",
    sorted(pathlib.Path("docs/data/contracts/semantic").glob("*.yaml"))
    + sorted(pathlib.Path("docs/data/contracts/semantic").glob("*.json")),
)
def test_metric_contract_valid(path: pathlib.Path) -> None:
    raw = path.read_text()
    # Tolerant YAML: accept both pure JSON and minimal YAML (key: value).
    obj = json.loads(raw) if path.suffix == ".json" else _simple_yaml_to_dict(raw)
    errors = _validate(obj)
    assert not errors, f"{path.name}: {errors}"


def _simple_yaml_to_dict(text: str) -> dict[str, Any]:
    """Tiny YAML subset parser for the metric contracts we author by hand."""

    out: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - "):
            assert current_list_key is not None
            val = line[4:].strip()
            if isinstance(out.get(current_list_key), list):
                out[current_list_key].append(val)
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            out[key] = []
            current_list_key = key
            continue
        current_list_key = None
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        out[key] = value
    return out
