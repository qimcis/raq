from __future__ import annotations

from typing import Any, Dict, List, Optional

from .datatypes import Relation
from .ra_ast import RAType, RARef, RASelect, RAProject, RAJoin, RASetOp
from .predicate import eval_predicate


def evaluate(node: RAType, rels: Dict[str, Relation]) -> Relation:
    if isinstance(node, RARef):
        if node.name not in rels:
            raise KeyError(f"Unknown relation: {node.name}")
        rel = rels[node.name]
        return Relation(name=node.name, header=list(rel.header), rows=[dict(r) for r in rel.rows])

    if isinstance(node, RASelect):
        child = evaluate(node.child, rels)
        out_rows: List[Dict[str, Any]] = []
        for r in child.rows:
            ctx = {k: v for k, v in r.items()}
            if eval_predicate(node.predicate, ctx):
                out_rows.append(dict(r))
        res = Relation(name=f"Select({child.name})", header=list(child.header), rows=out_rows)
        res.dedup()
        return res

    if isinstance(node, RAProject):
        child = evaluate(node.child, rels)
        for a in node.attrs:
            if a not in child.header:
                raise KeyError(f"Projection attribute '{a}' not in schema {child.header}")
        out_rows = [{a: r[a] for a in node.attrs} for r in child.rows]
        res = Relation(name=f"Project({child.name})", header=list(node.attrs), rows=out_rows)
        res.dedup()
        return res

    if isinstance(node, RAJoin):
        left = evaluate(node.left, rels)
        right = evaluate(node.right, rels)

        if node.predicate is None:
            common = [a for a in left.header if a in right.header]
            out_header = list(left.header) + [a for a in right.header if a not in common]
            out_rows: List[Dict[str, Any]] = []
            if common:
                for rl in left.rows:
                    for rr in right.rows:
                        if all(rl[a] == rr[a] for a in common):
                            merged = dict(rl)
                            for a in right.header:
                                if a not in common:
                                    merged[a] = rr[a]
                            out_rows.append(merged)
            else:
                for rl in left.rows:
                    for rr in right.rows:
                        merged = dict(rl)
                        for a in right.header:
                            merged[a] = rr[a]
                        out_rows.append(merged)
            res = Relation(name=f"Join({left.name},{right.name})", header=out_header, rows=out_rows)
            res.dedup()
            return res
        else:
            out_header = list(left.header)
            right_header_out: List[str] = []
            for a in right.header:
                if a in left.header:
                    right_header_out.append(f"{a}_right")
                else:
                    right_header_out.append(a)
            out_header += right_header_out

            out_rows: List[Dict[str, Any]] = []
            for rl in left.rows:
                for rr in right.rows:
                    ctx: Dict[str, Any] = {}
                    for a in left.header:
                        ctx[a] = rl[a]
                        ctx[f"left.{a}"] = rl[a]
                        ctx[f"{left.name}.{a}"] = rl[a]
                    for a in right.header:
                        if a not in ctx:
                            ctx[a] = rr[a]
                        ctx[f"right.{a}"] = rr[a]
                        ctx[f"{right.name}.{a}"] = rr[a]
                    if eval_predicate(node.predicate, ctx):
                        merged: Dict[str, Any] = {}
                        for a in left.header:
                            merged[a] = rl[a]
                        for a in right.header:
                            key = a if a not in left.header else f"{a}_right"
                            merged[key] = rr[a]
                        out_rows.append(merged)
            res = Relation(name=f"Join({left.name},{right.name})", header=out_header, rows=out_rows)
            res.dedup()
            return res

    if isinstance(node, RASetOp):
        left = evaluate(node.left, rels)
        right = evaluate(node.right, rels)
        if set(left.header) != set(right.header):
            raise ValueError(f"Set operation requires union-compatible schemas, got {left.header} vs {right.header}")
        if left.header != right.header:
            right = right.reorder_like(left.header)

        if node.op == 'union':
            rows = [dict(r) for r in left.rows] + [dict(r) for r in right.rows]
            res = Relation(name=f"Union({left.name},{right.name})", header=list(left.header), rows=rows)
            res.dedup()
            return res
        if node.op == 'intersect':
            set_right = {tuple(r[c] for c in right.header) for r in right.rows}
            out_rows = [dict(r) for r in left.rows if tuple(r[c] for c in left.header) in set_right]
            res = Relation(name=f"Intersect({left.name},{right.name})", header=list(left.header), rows=out_rows)
            res.dedup()
            return res
        if node.op == 'minus':
            set_right = {tuple(r[c] for c in right.header) for r in right.rows}
            out_rows = [dict(r) for r in left.rows if tuple(r[c] for c in left.header) not in set_right]
            res = Relation(name=f"Minus({left.name},{right.name})", header=list(left.header), rows=out_rows)
            res.dedup()
            return res
        raise ValueError(f"Unknown set operation: {node.op}")

    raise ValueError(f"Unsupported RA node: {node}")

