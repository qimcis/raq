from __future__ import annotations

import io
import csv
from typing import Any, List, Dict

from .datatypes import Relation


def _convert_value(tok: str) -> Any:
    s = tok.strip()
    if (len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"))):
        return s[1:-1]
    try:
        if s.lower().startswith("0x"):
            return int(s, 16)
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() in ("null", "none"):
        return None
    return s


def _parse_csv_row(line: str) -> List[str]:
    reader = csv.reader(io.StringIO(line), skipinitialspace=True)
    return next(reader)


def parse_definitions(text: str) -> Dict[str, Relation]:
    lines = text.splitlines()
    i = 0
    rels: Dict[str, Relation] = {}

    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if '(' in line and '=' in line and '{' in line:
            before_paren, after_paren_open = line.split('(', 1)
            name = before_paren.strip().split()[0]
            attrs_part, after_attrs = after_paren_open.split(')', 1)
            attrs = [a.strip() for a in attrs_part.split(',') if a.strip()]

            row_lines: List[str] = []
            while i < len(lines):
                ln = lines[i]
                i += 1
                if '}' in ln:
                    break
                stripped = ln.strip()
                if stripped:
                    if stripped.endswith(','):
                        stripped = stripped[:-1]
                    row_lines.append(stripped)

            rows: List[Dict[str, Any]] = []
            for rl in row_lines:
                if not rl:
                    continue
                cols = _parse_csv_row(rl)
                if len(cols) != len(attrs):
                    raise ValueError(f"Row arity mismatch for relation {name}: expected {len(attrs)} values, got {len(cols)} in line: {rl}")
                vals = [_convert_value(tok) for tok in cols]
                rows.append({attr: val for attr, val in zip(attrs, vals)})

            rel = Relation(name=name, header=list(attrs), rows=rows)
            rel.dedup()
            rels[name] = rel
    return rels

