"""Core IR node definitions and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Optional

from .pattern_match import IrPattern

if TYPE_CHECKING:
    from .ast_nodes import Node


class IrNode:
    """Base type for lowered Genia IR nodes."""


@dataclass
class IrAnnotation(IrNode):
    """Lowered annotation payload for a bindable definition."""

    name: str
    value: IrNode
    span: SourceSpan | None = None


@dataclass
class IrLiteral(IrNode):
    """Normalized constant value (number/string/bool/nil)."""

    value: Any
    span: SourceSpan | None = None


@dataclass
class IrOptionNone(IrNode):
    """Structured none value with optional quoted reason and evaluated context."""

    reason: IrNode | None = None
    context: IrNode | None = None
    span: SourceSpan | None = None


@dataclass
class IrOptionSome(IrNode):
    """Structured some value with explicit lowered inner value."""

    value: IrNode
    span: SourceSpan | None = None


@dataclass
class IrVar(IrNode):
    """Variable read by name (kept explicit for analysis and rewriting)."""

    name: str
    span: SourceSpan | None = None


@dataclass
class IrQuote(IrNode):
    """Quoted source expression preserved for syntax-to-data conversion."""

    expr: Node
    span: SourceSpan | None = None


@dataclass
class IrDelay(IrNode):
    """Delayed expression preserved for promise creation."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrQuasiQuote(IrNode):
    """Quasiquoted source expression preserved for syntax-to-data conversion."""

    expr: Node
    span: SourceSpan | None = None


@dataclass
class IrUnquote(IrNode):
    """Unquote special form; only valid during quasiquote processing."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrUnquoteSplicing(IrNode):
    """Unquote-splicing special form; only valid during quasiquote list processing."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrUnary(IrNode):
    """Unary operator application."""

    op: str
    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrBinary(IrNode):
    """Binary operator application with explicit operands."""

    left: IrNode
    op: str
    right: IrNode
    span: SourceSpan | None = None


@dataclass
class IrPipeline(IrNode):
    """Explicit pipeline source plus ordered stages for left-to-right evaluation."""

    source: IrNode
    stages: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrCall(IrNode):
    """Function call where callee and args are already lowered."""

    fn: IrNode
    args: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrExprStmt(IrNode):
    """Top-level expression statement (keeps source ordering explicit)."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrBlock(IrNode):
    """Sequential expression block."""

    exprs: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrList(IrNode):
    """List literal with lowered items."""

    items: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrMap(IrNode):
    """Map literal with lowered values and normalized string keys."""

    items: list[tuple[str, IrNode]]
    span: SourceSpan | None = None


@dataclass
class IrSpread(IrNode):
    """List spread element in expression contexts (list literals and call args)."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrCaseClause(IrNode):
    """Single case arm with optional guard."""

    pattern: IrPattern
    guard: Optional[IrNode]
    result: IrNode
    span: SourceSpan | None = None


@dataclass
class IrCase(IrNode):
    """Case dispatch is explicit so optimization passes can inspect patterns."""

    clauses: list[IrCaseClause]
    span: SourceSpan | None = None


@dataclass
class IrLambda(IrNode):
    """Lambda expression with params/pattern and lowered body."""

    params: list[str]
    rest_param: str | None
    body: IrNode
    span: SourceSpan | None = None
    pattern: IrPattern | None = None


@dataclass
class IrAssign(IrNode):
    """Top-level assignment side effect."""

    name: str
    expr: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrFuncDef(IrNode):
    """Named function definition with lowered body."""

    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrImport(IrNode):
    module_name: str
    alias: str
    span: SourceSpan | None = None


@dataclass
class IrShellStage(IrNode):
    """Shell pipeline stage — host-backed subprocess execution (experimental, Python-only)."""

    command: str
    span: SourceSpan | None = None


@dataclass
class IrListTraversalLoop(IrNode):
    """Optimized loop-like form for nth-style list traversal recursion."""

    counter_var: str
    list_var: str
    step_size: int
    empty_clause: IrCaseClause
    zero_clause: IrCaseClause
    span: SourceSpan | None = None


# Portable/shared Core IR node families produced by AST->IR lowering.
PORTABLE_CORE_IR_NODE_TYPES: tuple[type[IrNode], ...] = (
    IrAnnotation,
    IrLiteral,
    IrOptionNone,
    IrOptionSome,
    IrVar,
    IrQuote,
    IrDelay,
    IrQuasiQuote,
    IrUnquote,
    IrUnquoteSplicing,
    IrUnary,
    IrBinary,
    IrPipeline,
    IrCall,
    IrExprStmt,
    IrBlock,
    IrList,
    IrMap,
    IrSpread,
    IrCaseClause,
    IrCase,
    IrLambda,
    IrAssign,
    IrFuncDef,
    IrImport,
)

# Host-local post-lowering optimized nodes are intentionally outside the minimal portable contract.
HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES: tuple[type[IrNode], ...] = (
    IrListTraversalLoop,
)


def iter_ir_nodes(root: IrNode | Iterable[IrNode]) -> Iterator[IrNode]:
    """Yield IR nodes in depth-first order for validation and tooling."""
    if isinstance(root, IrNode):
        stack: list[IrNode] = [root]
    else:
        stack = list(root)

    while stack:
        node = stack.pop()
        yield node

        children: list[IrNode] = []
        if isinstance(node, IrOptionNone):
            if node.reason is not None:
                children.append(node.reason)
            if node.context is not None:
                children.append(node.context)
        elif isinstance(node, IrOptionSome):
            children.append(node.value)
        elif isinstance(node, IrDelay):
            children.append(node.expr)
        elif isinstance(node, IrUnquote):
            children.append(node.expr)
        elif isinstance(node, IrUnquoteSplicing):
            children.append(node.expr)
        elif isinstance(node, IrUnary):
            children.append(node.expr)
        elif isinstance(node, IrBinary):
            children.extend([node.left, node.right])
        elif isinstance(node, IrPipeline):
            children.append(node.source)
            children.extend(node.stages)
        elif isinstance(node, IrCall):
            children.append(node.fn)
            children.extend(node.args)
        elif isinstance(node, IrExprStmt):
            children.append(node.expr)
        elif isinstance(node, IrBlock):
            children.extend(node.exprs)
        elif isinstance(node, IrList):
            children.extend(node.items)
        elif isinstance(node, IrMap):
            children.extend(value for _, value in node.items)
        elif isinstance(node, IrSpread):
            children.append(node.expr)
        elif isinstance(node, IrCaseClause):
            if node.guard is not None:
                children.append(node.guard)
            children.append(node.result)
        elif isinstance(node, IrCase):
            children.extend(node.clauses)
        elif isinstance(node, IrLambda):
            children.append(node.body)
        elif isinstance(node, IrAssign):
            children.extend(annotation.value for annotation in node.annotations)
            children.append(node.expr)
        elif isinstance(node, IrFuncDef):
            children.extend(annotation.value for annotation in node.annotations)
            children.append(node.body)
        elif isinstance(node, IrListTraversalLoop):
            children.extend([node.empty_clause, node.zero_clause])

        stack.extend(reversed(children))


def assert_portable_core_ir(nodes: Iterable[IrNode]) -> None:
    """Raise when host-local post-lowering IR appears in a portable/lowered program."""
    for node in iter_ir_nodes(nodes):
        if isinstance(node, HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES):
            raise RuntimeError(
                "Portable Core IR validation failed: host-local post-lowering node "
                f"{type(node).__name__} appeared before host-local optimization."
            )
