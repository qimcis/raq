#!/usr/bin/env python3
import sys
from pathlib import Path

from raq import parse_definitions, parse_query, evaluate, print_relation


def read_input_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main(argv: list[str]) -> int:
    # Simple arg parsing to support a REPL mode
    if len(argv) >= 2 and argv[1] in ("--repl", "-i"):
        if len(argv) < 3:
            print("Usage: python3 main.py --repl <defs-file>")
            return 2
        defs_path = argv[2]
        return repl(defs_path)

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


def repl(defs_path: str) -> int:
    """Interactive loop: load relations once, then accept queries line-by-line.

    Commands:
      :help            Show help
      :rels            List loaded relation names
      :show <Rel>      Print a relation by name
      :reload          Reload definitions from the defs file
      :quit / :exit    Exit the REPL

    Query input:
      - Enter a relational algebra expression directly (σ/π/⋈/set ops or functional forms), or
      - Use the legacy prefix: `Query: <expr>`
    """
    try:
        text = read_input_text(defs_path)
    except Exception as e:
        print(f"Failed to read definitions file '{defs_path}': {e}")
        return 2

    relations = parse_definitions(text)
    print(f"Loaded {len(relations)} relations from {defs_path}. Type :help for help.")
    while True:
        try:
            line = input("raq> ").strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return 130

        if not line:
            continue
        if line.startswith(":"):
            cmd, *args = line[1:].strip().split()
            cmd = cmd.lower()
            if cmd in ("quit", "exit"):
                return 0
            if cmd == "help":
                print(
                    ":help, :rels, :show <Rel>, :reload, :quit"
                )
                continue
            if cmd == "rels":
                names = ", ".join(sorted(relations.keys())) or "(none)"
                print(names)
                continue
            if cmd == "show":
                if not args:
                    print("Usage: :show <RelationName>")
                    continue
                name = args[0]
                if name not in relations:
                    print(f"Unknown relation: {name}")
                    continue
                print_relation(relations[name])
                continue
            if cmd == "reload":
                try:
                    text = read_input_text(defs_path)
                    relations = parse_definitions(text)
                    print(f"Reloaded {len(relations)} relations from {defs_path}.")
                except Exception as e:
                    print(f"Reload failed: {e}")
                continue
            print(f"Unknown command: :{cmd}. Type :help")
            continue

        expr = line
        if line.lower().startswith("query:"):
            expr = line.split(":", 1)[1].strip()
        try:
            ast = parse_query(expr)
            result = evaluate(ast, relations)
            print_relation(result)
        except Exception as e:
            print(f"Error: {e}")
    # Unreachable
    # return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
