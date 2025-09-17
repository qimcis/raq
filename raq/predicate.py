from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .tokens import TOKEN


class PredNode:
    pass


@dataclass
class PConst(PredNode):
    value: Any


@dataclass
class PAttr(PredNode):
    name: str


@dataclass
class PUnary(PredNode):
    op: str  # 'not'
    expr: PredNode


@dataclass
class PBinary(PredNode):
    op: str  # 'and','or','==','!=','<','<=','>','>='
    left: PredNode
    right: PredNode


def parse_predicate(tokens: list[TOKEN]) -> PredNode:
    p = PredParser(tokens)
    expr = p.parse_expr(0)
    if p.peek() is not None:
        raise ValueError(f"Unexpected tokens after predicate: {p.peek()}")
    return expr


class PredParser:
    PRECEDENCE = {
        'or': 1,
        'and': 2,
        '==': 3, '=': 3, '!=': 3, '<': 3, '<=': 3, '>': 3, '>=': 3,
    }

    def __init__(self, tokens: list[TOKEN]):
        self.toks = tokens
        self.i = 0

    def peek(self) -> Optional[TOKEN]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def pop(self) -> TOKEN:
        if self.i >= len(self.toks):
            raise ValueError("Unexpected end of predicate")
        t = self.toks[self.i]
        self.i += 1
        return t

    def parse_expr(self, min_prec: int) -> PredNode:
        node = self.parse_unary()
        while True:
            tok = self.peek()
            if tok is None:
                break
            ttype, tval = tok
            op_norm: Optional[str] = None
            if ttype == 'OP' and tval in ('==', '=', '!=', '<', '<=', '>', '>='):
                op_norm = tval
            elif ttype == 'KW' and tval in ('and', 'or'):
                op_norm = tval
            elif ttype == 'OP' and tval in ('&&', '||'):
                op_norm = 'and' if tval == '&&' else 'or'
            else:
                break
            prec = self.PRECEDENCE[op_norm]
            if prec < min_prec:
                break
            self.pop()
            rhs = self.parse_expr(prec + 1)
            node = PBinary(op=op_norm, left=node, right=rhs)
        return node

    def parse_unary(self) -> PredNode:
        tok = self.peek()
        if tok and tok[0] == 'KW' and tok[1] == 'not':
            self.pop()
            expr = self.parse_unary()
            return PUnary(op='not', expr=expr)
        return self.parse_primary()

    def parse_primary(self) -> PredNode:
        tok = self.pop()
        ttype, tval = tok
        if ttype == 'LPAREN':
            node = self.parse_expr(0)
            if not self.peek() or self.peek()[0] != 'RPAREN':
                raise ValueError('Unbalanced parentheses in predicate')
            self.pop()
            return node
        if ttype == 'NUMBER':
            if '.' in tval:
                return PConst(float(tval))
            return PConst(int(tval))
        if ttype == 'STRING':
            return PConst(tval)
        if ttype == 'KW' and tval in ('true', 'false', 'null'):
            return PConst(True if tval == 'true' else False if tval == 'false' else None)
        if ttype == 'IDENT':
            name = tval
            # qualified attr
            # accept IDENT.DOT.IDENT optionally
            if self.peek() and self.peek()[0] == 'DOT':
                self.pop()
                nxt = self.pop()
                if nxt[0] != 'IDENT':
                    raise ValueError('Expected identifier after dot')
                name = f"{name}.{nxt[1]}"
            return PAttr(name)
        raise ValueError(f"Invalid token in predicate: {tok}")


def _lookup_attr(ctx: dict[str, Any], name: str) -> Any:
    if name in ctx:
        return ctx[name]
    if f"left.{name}" in ctx:
        return ctx[f"left.{name}"]
    if f"right.{name}" in ctx:
        return ctx[f"right.{name}"]
    raise KeyError(f"Attribute '{name}' not found in context")


def eval_predicate(pred: PredNode, ctx: dict[str, Any]) -> bool:
    if isinstance(pred, PConst):
        return bool(pred.value)
    if isinstance(pred, PAttr):
        val = _lookup_attr(ctx, pred.name)
        return bool(val)
    if isinstance(pred, PUnary):
        if pred.op == 'not':
            return not eval_predicate(pred.expr, ctx)
        raise ValueError(f"Unknown unary operator: {pred.op}")
    if isinstance(pred, PBinary):
        if pred.op in ('and', 'or'):
            l = eval_predicate(pred.left, ctx)
            if pred.op == 'and':
                return l and eval_predicate(pred.right, ctx)
            else:
                return l or eval_predicate(pred.right, ctx)
        lv = eval_value(pred.left, ctx)
        rv = eval_value(pred.right, ctx)
        if pred.op in ('==', '='):
            return lv == rv
        if pred.op == '!=':
            return lv != rv
        if pred.op == '<':
            return lv < rv
        if pred.op == '<=':
            return lv <= rv
        if pred.op == '>':
            return lv > rv
        if pred.op == '>=':
            return lv >= rv
        raise ValueError(f"Unknown binary operator: {pred.op}")
    raise ValueError(f"Unsupported predicate node: {pred}")


def eval_value(node: PredNode, ctx: dict[str, Any]) -> Any:
    if isinstance(node, PConst):
        return node.value
    if isinstance(node, PAttr):
        return _lookup_attr(ctx, node.name)
    return eval_predicate(node, ctx)

