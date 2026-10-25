"""Core IR node definitions and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Optional

from .pattern_match import IrPattern

if TYPE_CHECKING:
    from .ast_nodes import Node

SourceSpan = Any


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
    named_access: bool = False
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
class IrNamedPatternDef(IrNode):
    """Named pattern matcher definition lowered as a single-argument matcher."""

    name: str
    param: str
    body: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrImport(IrNode):
    module_name: str
    alias: str
    span: SourceSpan | None = None


@dataclass
class IrOpenFuncDef(IrNode):
    """R20 open-interface base unit: ordered IrCaseClause records reused
    verbatim from the existing case-dispatch representation. Grouped and
    repeated local clause syntax both normalize to this one node."""

    name: str
    clauses: list[IrCaseClause]
    docstring: str | None
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrOpenContribution(IrNode):
    """R20 one contributing module's ordered clause set targeting one open
    interface. Declaration only; performs no linking or invocation."""

    target_module_alias: str
    target_name: str
    clauses: list[IrCaseClause]
    span: SourceSpan | None = None


@dataclass
class IrOpenUse(IrNode):
    """R20 explicit contribution selection producing one immutable linked
    view bound to `local_name` in the declaring module only."""

    local_name: str
    target_module_alias: str
    target_name: str
    contribution_module_aliases: list[str]
    span: SourceSpan | None = None


@dataclass
class IrShellStage(IrNode):
    """Shell pipeline stage — host-backed subprocess execution (experimental, Python-only)."""

    command: str
    span: SourceSpan | None = None


@dataclass
class IrListTraversalLoop(IrNode):
    """Optimized loop-like form for nth-style list traversal recursion.

    The fast path is taken only for a numeric counter and a list argument; every other
    call evaluates the retained original `case` (retention-aware, domain-exact).
    """

    counter_var: str
    list_var: str
    step_size: int
    # The unoptimized grouped body, retained so the original arms (keys, ordinals,
    # guards, provenance) stay reachable and so evaluation can fall back to exact
    # case semantics outside the fast path's domain. Declared here (before the
    # recognized arms) only so a depth-first field walk meets the arms in source order.
    case: IrCase | None = field(default=None, kw_only=True)
    empty_clause: IrCaseClause
    zero_clause: IrCaseClause
    span: SourceSpan | None = None


@dataclass
class IrImmutableBind(IrNode):
    """Fresh current-scope declaration; Slice A rejects execution explicitly."""
    name: str
    expr: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrPatternFuncDef(IrNode):
    """One full tuple-pattern declaration, without a competing params channel."""
    name: str
    pattern: IrPattern
    guard: IrNode | None
    body: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrClosedFuncDef(IrNode):
    """Atomic nonempty same-name declaration records; not separately published."""
    name: str
    declarations: list[IrFuncDef | IrPatternFuncDef]
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
    IrImmutableBind,
    IrPatternFuncDef,
    IrClosedFuncDef,
    IrFuncDef,
    IrNamedPatternDef,
    IrImport,
    IrOpenFuncDef,
    IrOpenContribution,
    IrOpenUse,
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
        if isinstance(node, IrAnnotation):
            children.append(node.value)
        elif isinstance(node, IrClosedFuncDef):
            children.extend(node.declarations)
        elif isinstance(node, IrPatternFuncDef):
            children.extend(node.annotations)
            if node.guard is not None:
                children.append(node.guard)
            children.append(node.body)
        elif isinstance(node, (IrOpenFuncDef, IrOpenContribution)):
            children.extend(getattr(node, "annotations", []))
            children.extend(node.clauses)
        elif isinstance(node, IrOptionNone):
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
        elif isinstance(node, (IrAssign, IrImmutableBind)):
            children.extend(node.annotations)
            children.append(node.expr)
        elif isinstance(node, IrFuncDef):
            children.extend(node.annotations)
            children.append(node.body)
        elif isinstance(node, IrNamedPatternDef):
            children.extend(node.annotations)
            children.append(node.body)
        elif isinstance(node, IrListTraversalLoop):
            children.extend([node.empty_clause, node.zero_clause])

        stack.extend(reversed(children))


def assert_portable_core_ir(nodes: Iterable[IrNode]) -> None:
    """Validate lowered programs, including direct Model B declaration carriers.

    Reject malformed closed groups and pattern headers before a consumer can
    interpret them, and host-local optimized nodes at any executable IR depth.
    No annotation, guard, initializer or matcher is evaluated here.
    """
    for node in iter_ir_nodes(nodes):
        if isinstance(node, IrClosedFuncDef):
            if (not isinstance(node.declarations, list) or not node.declarations or any(type(child) not in (IrFuncDef, IrPatternFuncDef)
                    or child.name != node.name for child in node.declarations)):
                raise ValueError("invalid closed function declaration group")
        if isinstance(node, IrPatternFuncDef):
            _validate_model_b_pattern(node.pattern)
            if any(key in vars(node) for key in ("params", "rest_param", "docstring")):
                raise ValueError("pattern declaration has competing header representations")
            if isinstance(node.body, IrCase) or (isinstance(node.body, IrBlock)
                    and node.body.exprs and isinstance(node.body.exprs[-1], IrCase)):
                raise ValueError("pattern declaration cannot have a grouped case body")
        if isinstance(node, IrClosedFuncDef):
            for child in node.declarations:
                if any(isinstance(nested, (IrFuncDef, IrPatternFuncDef, IrClosedFuncDef))
                       for nested in iter_ir_nodes([child.body])):
                    raise ValueError("nested declarations in closed function body")
        if isinstance(node, (IrImmutableBind, IrPatternFuncDef)):
            expression = node.expr if isinstance(node, IrImmutableBind) else node.body
            if not isinstance(expression, IrNode):
                raise ValueError("invalid declaration expression")
            if (not isinstance(node.annotations, list)
                    or any(type(annotation) is not IrAnnotation for annotation in node.annotations)):
                raise ValueError("invalid declaration annotations")
            if isinstance(node, IrPatternFuncDef) and node.guard is not None and not isinstance(node.guard, IrNode):
                raise ValueError("invalid pattern declaration guard")
        if isinstance(node, (IrImmutableBind, IrPatternFuncDef, IrClosedFuncDef)):
            if not isinstance(node.name, str) or not node.name or "." in node.name:
                raise ValueError("invalid declaration name")

        if isinstance(node, HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES):
            raise RuntimeError(
                "Portable Core IR validation failed: host-local post-lowering node "
                f"{type(node).__name__} appeared before host-local optimization."
            )


def _validate_model_b_pattern(pattern: IrPattern) -> None:
    """Validate direct-IR full tuple headers recursively, without evaluating matchers.

    Reject expression carriers and unknown pattern subclasses at every depth.
    Existing R20/lambda parsers own source grammar; this protects bypass callers.
    """
    from dataclasses import fields
    from .pattern_match import (IrPatTuple, IrPatList, IrPatMap, IrPatBind,
        IrPatLiteral, IrPatWildcard, IrPatRest, IrPatSome, IrPatNone,
        IrPatErr, IrPatNamed, IrPatGlob)
    allowed = (IrPatTuple, IrPatList, IrPatMap, IrPatBind, IrPatLiteral,
               IrPatWildcard, IrPatRest, IrPatSome, IrPatNone, IrPatErr,
               IrPatNamed, IrPatGlob)
    if not isinstance(pattern, IrPatTuple):
        raise ValueError("function header pattern must be a tuple pattern")
    pending = [pattern]
    while pending:
        current = pending.pop()
        if type(current) not in allowed:
            raise ValueError("invalid function header pattern carrier")
        if isinstance(current, (IrPatTuple, IrPatList)):
            if any(isinstance(item, IrPatRest) for item in current.items[:-1]):
                raise ValueError("rest pattern must be final")
        for field_info in fields(current):
            value = getattr(current, field_info.name)
            if field_info.name == "items":
                pending.extend(item[1] if isinstance(item, tuple) else item for item in value)
            elif field_info.name in {"inner", "reason", "context"} and value is not None:
                pending.append(value)
