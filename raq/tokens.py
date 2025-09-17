from __future__ import annotations

from typing import List, Tuple, Optional


TOKEN = tuple[str, str]  # (type, value)


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == '_'


def _is_ident_part(ch: str) -> bool:
    return ch.isalnum() or ch == '_'


def tokenize(expr: str) -> List[TOKEN]:
    s = expr
    i = 0
    tokens: List[TOKEN] = []
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        # Strings
        if ch in ('"', "'"):
            quote = ch
            i += 1
            buf = []
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    buf.append(s[i + 1])
                    i += 2
                    continue
                if s[i] == quote:
                    i += 1
                    break
                buf.append(s[i])
                i += 1
            tokens.append(("STRING", ''.join(buf)))
            continue
        # Numbers
        if ch.isdigit():
            start = i
            while i < len(s) and (s[i].isdigit() or s[i] == '.'):
                i += 1
            tokens.append(("NUMBER", s[start:i]))
            continue
        # Multi-char operators
        two = s[i:i+2]
        if two in ("<=", ">=", "!=", "==", "&&", "||"):
            tokens.append(("OP", two))
            i += 2
            continue
        # Single-char tokens and symbols
        if ch in "()[]":
            ttype = { '(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACK', ']': 'RBRACK' }[ch]
            tokens.append((ttype, ch))
            i += 1
            continue
        if ch == ',':
            tokens.append(("COMMA", ch))
            i += 1
            continue
        if ch == '.':
            tokens.append(("DOT", ch))
            i += 1
            continue
        if ch == 'σ':
            tokens.append(("SIGMA", ch))
            i += 1
            continue
        if ch == 'π':
            tokens.append(("PI", ch))
            i += 1
            continue
        if ch == '⋈':
            tokens.append(("JOIN_SYM", ch))
            i += 1
            continue
        if ch in ('∪', '⋃'):
            tokens.append(("UNION_SYM", ch))
            i += 1
            continue
        if ch == '∩':
            tokens.append(("INTERSECT_SYM", ch))
            i += 1
            continue
        if ch in ('−', '-'):
            tokens.append(("DIFF_SYM", ch))
            i += 1
            continue
        if ch in ('<', '>', '='):
            tokens.append(("OP", ch))
            i += 1
            continue

        # Identifiers / keywords
        if _is_ident_start(ch):
            start = i
            i += 1
            while i < len(s) and _is_ident_part(s[i]):
                i += 1
            ident = s[start:i]
            low = ident.lower()
            if low in ("select", "project", "join", "union", "intersect", "minus", "on", "and", "or", "not", "true", "false", "null"):
                tokens.append(("KW", low))
            else:
                tokens.append(("IDENT", ident))
            continue

        if ch in ('¬', '∧', '∨'):
            mapping = {'¬': 'not', '∧': 'and', '∨': 'or'}
            tokens.append(("KW", mapping[ch]))
            i += 1
            continue

        raise ValueError(f"Unexpected character in expression: {ch}")

    return tokens

