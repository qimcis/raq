from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class RAType:
    pass


@dataclass
class RARef(RAType):
    name: str


@dataclass
class RASelect(RAType):
    predicate: "PredNode"
    child: RAType


@dataclass
class RAProject(RAType):
    attrs: List[str]
    child: RAType


@dataclass
class RAJoin(RAType):
    left: RAType
    right: RAType
    predicate: Optional["PredNode"]  # None => natural join


@dataclass
class RASetOp(RAType):
    op: str  # 'union' | 'intersect' | 'minus'
    left: RAType
    right: RAType

