"""Surface AST node definitions for the Python reference host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class Node:
    pass


@dataclass
class Number(Node):
    value: int | float
    span: SourceSpan | None = None


@dataclass
class String(Node):
    value: str
    span: SourceSpan | None = None


@dataclass
class Boolean(Node):
    value: bool
    span: SourceSpan | None = None


@dataclass
class Nil(Node):
    span: SourceSpan | None = None


@dataclass
class NoneOption(Node):
    reason: Node | None = None
    context: Node | None = None
    span: SourceSpan | None = None


@dataclass
class SymbolLiteral(Node):
    name: str
    span: SourceSpan | None = None


@dataclass
class Var(Node):
    name: str
    span: SourceSpan | None = None


@dataclass
class Quote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Delay(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class QuasiQuote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Unquote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class UnquoteSplicing(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Unary(Node):
    op: str
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node
    span: SourceSpan | None = None


@dataclass
class Call(Node):
    fn: Node
    args: list[Node]
    span: SourceSpan | None = None


@dataclass
class ExprStmt(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Block(Node):
    exprs: list[Node]
    span: SourceSpan | None = None


@dataclass
class ListLiteral(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class MapLiteral(Node):
    items: list[tuple[Node, Node]]
    span: SourceSpan | None = None


@dataclass
class Spread(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class ListPattern(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class GlobPattern(Node):
    pattern: str
    span: SourceSpan | None = None


@dataclass
class WildcardPattern(Node):
    span: SourceSpan | None = None


@dataclass
class RestPattern(Node):
    name: str | None
    span: SourceSpan | None = None


@dataclass
class TuplePattern(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class MapPattern(Node):
    items: list[tuple[str, Node]]
    span: SourceSpan | None = None


@dataclass
class SomePattern(Node):
    inner: Node
    span: SourceSpan | None = None


@dataclass
class CaseClause(Node):
    pattern: Node
    guard: Optional[Node]
    result: Node
    span: SourceSpan | None = None


@dataclass
class CaseExpr(Node):
    clauses: list[CaseClause]
    span: SourceSpan | None = None


@dataclass
class Lambda(Node):
    params: list[str]
    rest_param: str | None
    body: Node
    span: SourceSpan | None = None
    pattern: Node | None = None


@dataclass
class Assign(Node):
    name: str
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Annotation(Node):
    name: str
    value: Node
    span: SourceSpan | None = None


@dataclass
class AnnotatedNode(Node):
    annotations: list[Annotation]
    target: Node
    span: SourceSpan | None = None


@dataclass
class FuncDef(Node):
    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: Node
    span: SourceSpan | None = None


@dataclass
class ImportStmt(Node):
    module_name: str
    alias: str
    span: SourceSpan | None = None


@dataclass
class ShellStage(Node):
    command: str
    span: SourceSpan | None = None
