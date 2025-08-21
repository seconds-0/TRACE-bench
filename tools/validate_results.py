#!/usr/bin/env python3
"""
Validate TRACE results (JSON or JSONL) against the schema.

Usage:
  python tools/validate_results.py <path-to-json-or-jsonl>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import jsonschema


def load_schema() -> dict[str, Any]:
    schema_path = Path("schemas/trace-result.schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_json(path: Path) -> Iterable[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        for i, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:  # noqa: TRY003
                raise SystemExit(f"Invalid JSON on line {i}: {e}")
    else:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Invalid JSON: {e}")
        yield obj


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate TRACE result JSON/JSONL")
    ap.add_argument("path", type=Path)
    args = ap.parse_args()

    schema = load_schema()
    count = 0
    for obj in iter_json(args.path):
        jsonschema.validate(instance=obj, schema=schema)
        count += 1

    print(f"Validated {count} record(s) against schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

