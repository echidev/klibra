from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DependencyCheck:
    name: str
    ok: bool
    details: str = ""


def check_health() -> dict[str, Any]:
    return {"status": "ok"}


def check_ready(deps: list[DependencyCheck] | None = None) -> dict[str, Any]:
    deps = deps or []
    failed = [d for d in deps if not d.ok]
    if failed:
        return {"status": "degraded", "dependencies": [{"name": d.name, "ok": d.ok, "details": d.details} for d in failed]}
    return {"status": "ok", "dependencies": []}
