from __future__ import annotations

from typing import List, Optional, Tuple

from .tokens import tokenize, TOKEN
from .ra_ast import RAType, RARef, RASelect, RAProject, RAJoin, RASetOp
from .predicate import PredNode, parse_predicate


class Parser:
    def __init__(self, tokens: List[TOKEN]):
        self.toks = tokens
        self.i = 0

    def peek(self) -> Optional[TOKEN]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def pop(self) -> TOKEN:
        if self.i >= len(self.toks):
            raise ValueError("Unexpected end of input")
        t = self.toks[self.i]
        self.i += 1
        return t

    def match(self, *types_vals: Tuple[str, Optional[str]]):
        if self.i >= len(self.toks):
            return None
        ttype, tval = self.toks[self.i]
        for tv in types_vals:
            ty, val = tv
            if ttype == ty and (val is None or tval == val):
                self.i += 1
                return (ttype, tval)
        return None

    def expect(self, ttype: str, value: Optional[str] = None) -> TOKEN:
        tok = self.pop()
        if tok[0] != ttype or (value is not None and tok[1] != value):
            raise ValueError(f"Expected {ttype} {value or ''} but got {tok}")
        return tok

    def parse_rel_expr(self) -> RAType:
        return self._parse_set_level()

    def _parse_set_level(self) -> RAType:
        left = self._parse_join_level()
        while True:
            tok = self.peek()
            if tok is None:
                break
            ttype, tval = tok
            if ttype in ("UNION_SYM",) or (ttype == "KW" and tval == "union"):
                self.pop()
                right = self._parse_join_level()
                left = RASetOp("union", left, right)
                continue
            if ttype in ("INTERSECT_SYM",) or (ttype == "KW" and tval == "intersect"):
                self.pop()
                right = self._parse_join_level()
                left = RASetOp("intersect", left, right)
                continue
            if ttype in ("DIFF_SYM",) or (ttype == "KW" and tval == "minus"):
                self.pop()
                right = self._parse_join_level()
                left = RASetOp("minus", left, right)
                continue
            break
        return left

    def _parse_join_level(self) -> RAType:
        left = self._parse_unary_level()
        while True:
            tok = self.peek()
            if tok and tok[0] == "JOIN_SYM":
                self.pop()
                pred: Optional[PredNode] = None
                if self.match(("LBRACK", None)):
                    pred_tokens = self._collect_until_matching_bracket()
                    pred = parse_predicate(pred_tokens)
                    self.expect("RBRACK")
                right = self._parse_unary_level()
                left = RAJoin(left=left, right=right, predicate=pred)
                continue
            break
        return left

    def _parse_unary_level(self) -> RAType:
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of input in expression")
        ttype, tval = tok

        # Functional set ops
        if ttype == "KW" and tval in ("union", "intersect", "minus"):
            self.pop()
            self.expect("LPAREN")
            left = self.parse_rel_expr()
            self.expect("COMMA")
            right = self.parse_rel_expr()
            self.expect("RPAREN")
            return RASetOp(op=tval, left=left, right=right)

        # Functional join with optional predicate either in brackets or as third arg
        if ttype == "KW" and tval == "join":
            self.pop()
            pred: Optional[PredNode] = None
            if self.match(("LBRACK", None)):
                pred_tokens = self._collect_until_matching_bracket()
                pred = parse_predicate(pred_tokens)
                self.expect("RBRACK")
            self.expect("LPAREN")
            left = self.parse_rel_expr()
            self.expect("COMMA")
            right = self.parse_rel_expr()
            if self.peek() and self.peek()[0] == "COMMA":
                self.pop()
                pred_tokens: List[TOKEN] = []
                depth = 0
                while True:
                    tok2 = self.peek()
                    if tok2 is None:
                        raise ValueError("Unclosed predicate in join(...)")
                    if tok2[0] == 'LPAREN':
                        depth += 1
                        pred_tokens.append(self.pop())
                        continue
                    if tok2[0] == 'RPAREN':
                        if depth == 0:
                            break
                        depth -= 1
                        pred_tokens.append(self.pop())
                        continue
                    pred_tokens.append(self.pop())
                if pred is not None:
                    raise ValueError("Join predicate specified both in brackets and as third argument")
                pred = parse_predicate(pred_tokens)
            self.expect("RPAREN")
            return RAJoin(left=left, right=right, predicate=pred)

        # Selection
        if (ttype == "SIGMA") or (ttype == "KW" and tval == "select"):
            self.pop()
            pred_tokens = self._collect_until_child_lparen()
            predicate = parse_predicate(pred_tokens)
            self.expect("LPAREN")
            child = self.parse_rel_expr()
            self.expect("RPAREN")
            return RASelect(predicate=predicate, child=child)

        # Projection
        if (ttype == "PI") or (ttype == "KW" and tval == "project"):
            self.pop()
            attr_tokens = self._collect_until_child_lparen()
            attrs = _parse_attr_list(attr_tokens)
            self.expect("LPAREN")
            child = self.parse_rel_expr()
            self.expect("RPAREN")
            return RAProject(attrs=attrs, child=child)

        # Parenthesized
        if self.match(("LPAREN", None)):
            inner = self.parse_rel_expr()
            self.expect("RPAREN")
            return inner

        ident = self.match(("IDENT", None))
        if ident:
            return RARef(name=ident[1])

        raise ValueError(f"Unexpected token in expression: {tok}")

    def _collect_until_child_lparen(self) -> List[TOKEN]:
        collected: List[TOKEN] = []
        depth = 0  # parentheses depth inside predicate text
        while True:
            tok = self.peek()
            if tok is None:
                break
            ttype, _ = tok
            # If we see an LPAREN:
            if ttype == "LPAREN":
                prev = collected[-1] if collected else None
                # If we are not currently inside predicate parentheses and
                # the previous token ends a predicate (IDENT/NUMBER/STRING/RPAREN),
                # then this LPAREN is the start of the child expression.
                if depth == 0 and prev is not None and (
                    prev[0] in ("IDENT", "NUMBER", "STRING", "RPAREN") or
                    (prev[0] == "KW" and prev[1] in ("true", "false", "null"))
                ):
                    break
                # Otherwise, treat it as predicate grouping
                depth += 1
                collected.append(self.pop())
                continue
            # Closing parenthesis: close predicate grouping if any
            if ttype == "RPAREN":
                if depth == 0:
                    # Unbalanced close - let the predicate parser surface an error later
                    break
                depth -= 1
                collected.append(self.pop())
                continue
            # Otherwise, token is part of predicate
            collected.append(self.pop())
        return collected

    def _collect_until_matching_bracket(self) -> List[TOKEN]:
        collected: List[TOKEN] = []
        depth = 1
        while True:
            tok = self.peek()
            if tok is None:
                raise ValueError("Unclosed bracket in join predicate")
            if tok[0] == "LBRACK":
                depth += 1
                collected.append(self.pop())
                continue
            if tok[0] == "RBRACK":
                depth -= 1
                if depth == 0:
                    break
                collected.append(self.pop())
                continue
            collected.append(self.pop())
        return collected


def _parse_attr_list(tokens: List[TOKEN]) -> List[str]:
    attrs: List[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t[0] == 'IDENT':
            attrs.append(t[1])
            i += 1
            if i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
            continue
        if t[0] == 'COMMA' or t[0] in ('LPAREN', 'RPAREN'):
            i += 1
            continue
        raise ValueError(f"Invalid attribute list near token {t}")
    if not attrs:
        raise ValueError("Projection requires at least one attribute")
    return attrs


def parse_query(expr: str) -> RAType:
    tokens = tokenize(expr)
    parser = Parser(tokens)
    ast = parser.parse_rel_expr()
    if parser.peek() is not None:
        raise ValueError(f"Unexpected input after end of expression: {parser.peek()}")
    return ast
