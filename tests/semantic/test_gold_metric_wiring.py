"""Contract test ensuring Gold models reference metrics only by ``metric_id``.

Per FR-C-6 002-C: every Gold model that consumes a semantic metric must
reference the metric by ``metric_id`` only, never by a hard-coded
``version`` string literal. This script scans Gold SQL files for the
pattern ``metric_id = 'X' AND version = 'Y'`` which would indicate a
version-pinned reference.
"""

from __future__ import annotations

import pathlib
import re

GOLD_DIR = pathlib.Path("transformation/gold/models")
VERSION_PIN_PATTERN = re.compile(r"""version\s*=\s*['"][^'"]+['"]""", re.IGNORECASE)


def test_gold_models_do_not_hardcode_metric_versions() -> None:
    if not GOLD_DIR.exists():
        # No Gold models yet — vacuously pass.
        return
    violations: list[str] = []
    for path in GOLD_DIR.glob("**/*.sql"):
        text = path.read_text()
        # Only check lines that mention a metric_id column.
        if "metric_id" not in text:
            continue
        for match in VERSION_PIN_PATTERN.finditer(text):
            # Allow dbt config() or string literals unrelated to metrics
            line = text[max(0, match.start() - 80) : match.end() + 80]
            if "metric" in line.lower() or "version" in line.lower():
                violations.append(
                    f"{path}:{line.count(chr(10), 0, match.start())}: hard-coded version near metric: {line!r}"
                )
    assert not violations, "Gold models must reference metrics by metric_id only: " + "\n".join(
        violations
    )
