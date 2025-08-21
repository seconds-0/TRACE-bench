#!/usr/bin/env python3
"""
Generate a small mock suite run and write JSONL + aggregate JSON for validation.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import sys

# Ensure project root on path for package imports when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trace.evaluation.suite import BenchmarkSuite
from trace.models.mock import MockModel


def main() -> int:
    out_dir = Path("tmp")
    out_dir.mkdir(exist_ok=True)
    jsonl = out_dir / "results.jsonl"
    agg = out_dir / "aggregate.json"

    model = MockModel(mode="final", perfect=True)
    suite = BenchmarkSuite(model)
    results = suite.run_suite("trivial", 2, mode="final", jsonl_path=str(jsonl))
    suite.save_results(results, str(agg))
    print(f"Wrote {jsonl} and {agg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
