#!/usr/bin/env python3
import sys
from pathlib import Path

from raq import parse_definitions, parse_query, evaluate, print_relation


def read_input_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else None
    text = read_input_text(path)

    relations = parse_definitions(text)

    # Gather queries: lines starting with "Query:"; take remainder as single-line expr
    queries: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("Query:"):
            queries.append(line.split(":", 1)[1].strip())

    if not queries:
        print("No queries found. Add lines like: 'Query: σ Age > 30 (Employees)'")
        return 1

    for idx, q in enumerate(queries, 1):
        print(f"\n=== Query {idx} ===\n{q}")
        ast = parse_query(q)
        result = evaluate(ast, relations)
        print()
        print_relation(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
