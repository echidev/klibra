"""Backfill CLI — Spec 004 T039.

Usage::

    python -m orchestration.operators.backfill_cli \\
        --dataset worldbank:EXR.M.USD.EUR.SP00.A \\
        --start 2023-01-01 \\
        --end 2023-01-07 \\
        --reason "Re-extract after schema change" \\
        --requested-by alice@klibra.local \\
        --code-version 0.1.0 \\
        --expected-impact minor_correction
"""

from __future__ import annotations

import argparse
import json
import sys

from orchestration.operators.backfill_orchestrator import (
    BackfillOrchestrator,
    BackfillRequest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="backfill_cli",
        description="Submit a BackfillRequest and print the orchestrator receipt.",
    )
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--start", required=True, help="ISO date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="ISO date YYYY-MM-DD")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--requested-by", required=True)
    parser.add_argument("--code-version", required=True)
    parser.add_argument("--expected-impact", required=True)
    args = parser.parse_args(argv)

    req = BackfillRequest(
        dataset=args.dataset,
        start_period=args.start,
        end_period=args.end,
        reason=args.reason,
        requested_by=args.requested_by,
        code_version=args.code_version,
        expected_impact=args.expected_impact,
    )
    is_valid, errors = BackfillOrchestrator.validate(req)
    if not is_valid:
        print(json.dumps({"status": "REJECTED", "errors": errors}, indent=2))
        return 1
    receipt = BackfillOrchestrator().submit(req)
    print(json.dumps(receipt, indent=2, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
