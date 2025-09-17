from __future__ import annotations

from typing import Any

from .datatypes import Relation


def print_relation(rel: Relation) -> None:
    print(f"{rel.name} = {{{', '.join(rel.header)}")
    for r in rel.rows:
        vals = [repr_value(r[c]) for c in rel.header]
        print("  " + ", ".join(vals))
    print("}")

    print()
    print("\t".join(rel.header))
    for r in rel.rows:
        print("\t".join(stringify_cell(r[c]) for c in rel.header))


def repr_value(v: Any) -> str:
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def stringify_cell(v: Any) -> str:
    if v is None:
        return "NULL"
    return str(v)

