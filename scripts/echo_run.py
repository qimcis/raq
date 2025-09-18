#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when running from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from raq import parse_definitions, parse_query, evaluate, print_relation


def main(argv: list[str]) -> int:
    # Accept optional path; default to examples/test.txt if present
    if len(argv) < 2:
        default = ROOT / 'examples' / 'test.txt'
        if default.exists():
            path = str(default)
        else:
            print("Usage: python3 scripts/echo_run.py <input-file>")
            return 2
    else:
        path = argv[1]
    text = Path(path).read_text(encoding="utf-8")

    print("=== Input ===")
    print(text.rstrip())

    relations = parse_definitions(text)

    queries: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("Query:"):
            queries.append(line.split(":", 1)[1].strip())

    if not queries:
        print("No queries found. Add lines like: 'Query: σ Age > 30 (Employees)'")
        return 1

    print("\n=== Output ===")
    for idx, q in enumerate(queries, 1):
        print(f"\n--- Query {idx} ---\n{q}")
        ast = parse_query(q)
        result = evaluate(ast, relations)
        print_relation(result)
        print(f"Rows: {len(result.rows)}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
