"""Pure typed structural keys for function-clause headers (Model B, issue #1269).

LANGUAGE CONTRACT: two clause headers collide for duplicate detection exactly
when their pattern and guard structures are equal up to bound-variable
spelling. Literal tags (Boolean, Integer, floating, string, tagged numeric
payload) stay distinct, quoted syntax is data, and only active unquotes are
expression references.

PYTHON REFERENCE HOST: one explicit, allow-listed walker over lowered Core IR,
patterns and quoted surface syntax. It never evaluates, renders (`repr`/`str`),
hashes by host equality, or falls back for unknown values; unsupported or
malformed input raises ``TypeError``/``ValueError``.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional

from . import ast_nodes, ir, pattern_match
from .pattern_match import (
    CompiledGlobPattern,
    GlobClassEntry,
    GlobToken,
    IrPatBind,
    IrPatRest,
    IrPatTuple,
)

_SPAN_FIELDS = frozenset({"span"})

# Nodes whose structure is known and walked field-by-field. Host-local optimized
# nodes (`IrListTraversalLoop`) are deliberately absent: they never appear in
# pre-optimization headers, and an unknown class must not get a repr-based key.
_IR_CLASSES = frozenset(
    cls
    for cls in vars(ir).values()
    if isinstance(cls, type) and issubclass(cls, ir.IrNode) and cls is not ir.IrNode and dataclasses.is_dataclass(cls)
) - {ir.IrListTraversalLoop}
_PATTERN_CLASSES = frozenset(
    cls
    for cls in vars(pattern_match).values()
    if isinstance(cls, type)
    and issubclass(cls, pattern_match.IrPattern)
    and cls is not pattern_match.IrPattern
    and dataclasses.is_dataclass(cls)
)
_AUX_CLASSES = frozenset({CompiledGlobPattern, GlobClassEntry, GlobToken})
_AST_CLASSES = frozenset(
    cls
    for cls in vars(ast_nodes).values()
    if isinstance(cls, type) and issubclass(cls, ast_nodes.Node) and cls is not ast_nodes.Node and dataclasses.is_dataclass(cls)
)


def collect_pattern_binders(node: Any, order: list[str]) -> None:
    """Append every `IrPatBind`/named `IrPatRest` binder name in first-occurrence order.

    Walks dataclass fields generically; non-dataclass values contribute nothing.
    """
    if node is None:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            collect_pattern_binders(item, order)
        return
    if not dataclasses.is_dataclass(node) or isinstance(node, type):
        return
    if isinstance(node, IrPatBind):
        if node.name not in order:
            order.append(node.name)
        return
    if isinstance(node, IrPatRest):
        if node.name is not None and node.name not in order:
            order.append(node.name)
        return
    for field in dataclasses.fields(node):
        if field.name in _SPAN_FIELDS:
            continue
        collect_pattern_binders(getattr(node, field.name), order)


def clause_shape(pattern: Any) -> tuple[str, int]:
    """Return ``("fixed", n)`` or ``("varargs", minimum)`` for a well-formed tuple pattern.

    Raises ``TypeError`` for anything but an `IrPatTuple` whose items are a list of
    pattern nodes, so a malformed header never becomes fixed arity zero.
    """
    if type(pattern) is not IrPatTuple:
        raise TypeError("function header pattern must be a tuple pattern")
    items = pattern.items
    if not isinstance(items, list):
        raise TypeError("function header pattern items must be a list")
    for item in items:
        if type(item) not in _PATTERN_CLASSES:
            raise TypeError("function header pattern item is not a pattern node")
    if items and isinstance(items[-1], IrPatRest):
        return ("varargs", len(items) - 1)
    return ("fixed", len(items))


def _next_ordinal(scope: dict[str, int]) -> int:
    return max(scope.values(), default=-1) + 1


def _bind(scope: dict[str, int], names: list[str]) -> dict[str, int]:
    """Return a child scope that gives each of `names` a fresh ordinal (later shadows earlier)."""
    child = dict(scope)
    for name in names:
        child[name] = _next_ordinal(child)
    return child


def _literal_key(value: Any) -> Any:
    """Tagged key of one literal payload; payload mappings are order-independent."""
    if value is None:
        return ("nil",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, float):
        return ("float", value.hex() if value == value else "nan")
    if isinstance(value, str):
        return ("str", value)
    if isinstance(value, dict):
        entries = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("unsupported literal payload key")
            entries.append((key, _literal_key(item)))
        return ("payload", tuple(sorted(entries, key=lambda entry: entry[0])))
    if isinstance(value, (list, tuple)):
        return ("seq", tuple(_literal_key(item) for item in value))
    raise TypeError(f"unsupported literal payload type {type(value).__name__}")


def _scalar_key(value: Any) -> Any:
    """Tagged key of a non-node field value (names, operators, flags)."""
    if value is None:
        return ("nil",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, float):
        return ("float", value.hex() if value == value else "nan")
    if isinstance(value, str):
        return ("str", value)
    raise TypeError(f"unsupported key value type {type(value).__name__}")


def _is_node_like(value: Any) -> bool:
    return dataclasses.is_dataclass(value) and not isinstance(value, type)


def structural_key(node: Any, scope: dict[str, int]) -> Any:
    """Structural, span-free, alpha-normalized, type-tagged key of one IR/pattern node.

    `scope` maps pattern-bound names to ordinals; references keep the ordinal, free
    names stay syntactic, nested binders (lambda parameters, case-clause patterns,
    function definitions) receive fresh ordinals so their spelling never matters.
    """
    return _walk(node, scope, 0)


def _walk(node: Any, scope: dict[str, int], depth: int) -> Any:
    if node is None:
        return ("nil",)
    if isinstance(node, (list, tuple)):
        return ("seq", tuple(_walk(item, scope, depth) for item in node))
    if not _is_node_like(node):
        return _scalar_key(node)
    cls = type(node)
    if cls in _PATTERN_CLASSES:
        return _pattern_key(node, scope)
    if cls in _AUX_CLASSES:
        return _fields_key(node, scope, depth)
    if cls in _AST_CLASSES:
        return _ast_key(node, scope, 0, False)
    if cls not in _IR_CLASSES:
        raise TypeError(f"unsupported node type {cls.__name__} in a dispatch key")
    if cls is ir.IrLiteral:
        return ("IrLiteral", _literal_key(node.value))
    if cls is ir.IrVar:
        if node.name in scope:
            return ("BINDREF", scope[node.name])
        return ("IrVar", ("str", node.name))
    if cls in (ir.IrQuote,):
        return ("IrQuote", _ast_key(node.expr, scope, 0, True))
    if cls is ir.IrQuasiQuote:
        return ("IrQuasiQuote", _ast_key(node.expr, scope, 1, True))
    if cls is ir.IrLambda:
        return _lambda_key(node, scope, depth)
    if cls is ir.IrCaseClause:
        names: list[str] = []
        collect_pattern_binders(node.pattern, names)
        inner = _bind(scope, names)
        return (
            "IrCaseClause",
            _pattern_key(node.pattern, inner),
            None if node.guard is None else _walk(node.guard, inner, depth),
            _walk(node.result, inner, depth),
        )
    if cls is ir.IrBlock:
        return _block_key(node, scope, depth)
    if cls is ir.IrAssign:
        target = ("BINDREF", scope[node.name]) if node.name in scope else ("str", node.name)
        return (
            "IrAssign",
            target,
            _walk(node.expr, scope, depth),
            _walk(node.annotations, scope, depth),
        )
    if cls is ir.IrFuncDef:
        inner = _bind(scope, list(node.params) + ([node.rest_param] if node.rest_param is not None else []))
        return (
            "IrFuncDef",
            _scalar_key(node.name),
            len(node.params),
            node.rest_param is not None,
            _scalar_key(node.docstring),
            _walk(node.body, inner, depth),
            _walk(node.annotations, scope, depth),
        )
    if cls is ir.IrNamedPatternDef:
        inner = _bind(scope, [node.param])
        return (
            "IrNamedPatternDef",
            _scalar_key(node.name),
            _walk(node.body, inner, depth),
            _walk(node.annotations, scope, depth),
        )
    return _fields_key(node, scope, depth)


def _fields_key(node: Any, scope: dict[str, int], depth: int) -> tuple:
    parts: list[Any] = [type(node).__name__]
    for field in dataclasses.fields(node):
        if field.name in _SPAN_FIELDS:
            continue
        parts.append(_walk(getattr(node, field.name), scope, depth))
    return tuple(parts)


def _lambda_key(node: ir.IrLambda, scope: dict[str, int], depth: int) -> tuple:
    names = list(node.params)
    if node.rest_param is not None:
        names.append(node.rest_param)
    if node.pattern is not None:
        collect_pattern_binders(node.pattern, names)
    inner = _bind(scope, names)
    return (
        "IrLambda",
        len(node.params),
        node.rest_param is not None,
        None if node.pattern is None else _pattern_key(node.pattern, inner),
        _walk(node.body, inner, depth),
    )


def _block_key(node: ir.IrBlock, scope: dict[str, int], depth: int) -> tuple:
    return ("IrBlock", tuple(_walk(expr, scope, depth) for expr in node.exprs))


def _pattern_key(node: Any, scope: dict[str, int]) -> Any:
    if node is None:
        return ("nil",)
    cls = type(node)
    if cls not in _PATTERN_CLASSES:
        raise TypeError(f"unsupported pattern node type {cls.__name__}")
    if cls is IrPatBind:
        if node.name in scope:
            return ("BIND", scope[node.name])
        return ("IrPatBind", ("str", node.name))
    if cls is IrPatRest:
        if node.name is not None and node.name in scope:
            return ("RESTBIND", scope[node.name])
        return ("IrPatRest", _scalar_key(node.name))
    if cls is pattern_match.IrPatLiteral:
        return ("IrPatLiteral", _literal_key(node.value))
    parts: list[Any] = [cls.__name__]
    for field in dataclasses.fields(node):
        value = getattr(node, field.name)
        parts.append(_pattern_field_key(value, scope))
    return tuple(parts)


def _pattern_field_key(value: Any, scope: dict[str, int]) -> Any:
    if value is None:
        return ("nil",)
    if isinstance(value, (list, tuple)):
        return ("seq", tuple(_pattern_field_key(item, scope) for item in value))
    if _is_node_like(value):
        if type(value) in _PATTERN_CLASSES:
            return _pattern_key(value, scope)
        if type(value) in _AUX_CLASSES:
            return _fields_key(value, scope, 0)
        raise TypeError(f"unsupported pattern field type {type(value).__name__}")
    return _scalar_key(value)


def _ast_key(node: Any, scope: dict[str, int], quote_depth: int, data: bool) -> Any:
    """Key of quoted surface syntax. Quoted syntax is data; the only references
    are unquotes active at quasiquote depth zero, walked as expressions."""
    if node is None:
        return ("nil",)
    if isinstance(node, (list, tuple)):
        return ("seq", tuple(_ast_key(item, scope, quote_depth, data) for item in node))
    if not _is_node_like(node):
        return _literal_key(node)
    cls = type(node)
    if cls not in _AST_CLASSES:
        raise TypeError(f"unsupported syntax node type {cls.__name__}")
    if cls is ast_nodes.QuasiQuote:
        return ("QuasiQuote", _ast_key(node.expr, scope, quote_depth + 1, True))
    if cls in (ast_nodes.Unquote, ast_nodes.UnquoteSplicing) and quote_depth > 0:
        if quote_depth == 1:
            return (cls.__name__, _ast_key(node.expr, scope, 0, False))
        return (cls.__name__, _ast_key(node.expr, scope, quote_depth - 1, True))
    if not data and cls is ast_nodes.Var and node.name in scope:
        return ("BINDREF", scope[node.name])
    if not data and cls is ast_nodes.Lambda:
        names = list(node.params) + ([node.rest_param] if node.rest_param is not None else [])
        inner = _bind(scope, names)
        return (
            "Lambda",
            len(node.params),
            node.rest_param is not None,
            _ast_key(node.body, inner, quote_depth, data),
        )
    parts: list[Any] = [cls.__name__]
    for field in dataclasses.fields(node):
        if field.name in _SPAN_FIELDS:
            continue
        parts.append(_ast_key(getattr(node, field.name), scope, quote_depth, data))
    return tuple(parts)


def open_dispatch_key(pattern: Any, guard: Optional[ir.IrNode]) -> tuple:
    """Return ``(shape, pattern key, guard key)`` for one clause header.

    Spans, bodies and closures are excluded; only pattern-bound names are
    normalized. Nothing is evaluated or rendered. Raises on malformed or
    unsupported input.
    """
    shape = clause_shape(pattern)
    order: list[str] = []
    collect_pattern_binders(pattern, order)
    scope = {name: index for index, name in enumerate(order)}
    return (
        shape,
        _pattern_key(pattern, scope),
        structural_key(guard, scope) if guard is not None else None,
    )
