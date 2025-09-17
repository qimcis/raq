from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class Relation:
    name: str
    header: List[str]
    rows: List[Dict[str, Any]]

    def copy_with(self, name: Optional[str] = None, header: Optional[List[str]] = None, rows: Optional[List[Dict[str, Any]]] = None) -> "Relation":
        return Relation(name or self.name, header or list(self.header), rows or [dict(r) for r in self.rows])

    def dedup(self) -> None:
        seen: set[Tuple[Any, ...]] = set()
        new_rows: List[Dict[str, Any]] = []
        for r in self.rows:
            t = tuple(r.get(c) for c in self.header)
            if t not in seen:
                seen.add(t)
                new_rows.append(r)
        self.rows = new_rows

    def reorder_like(self, header: List[str]) -> "Relation":
        assert set(self.header) == set(header), "Schemas must match to reorder"
        new_rows = [{c: row[c] for c in header} for row in self.rows]
        return Relation(self.name, list(header), new_rows)

