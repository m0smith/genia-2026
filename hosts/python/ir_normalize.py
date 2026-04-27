"""
Portable Core IR normalization for shared semantic specs.
"""

from __future__ import annotations

from typing import Any, Iterable

from genia.interpreter import (
    Boolean,
    IrAnnotation,
    IrAssign,
    IrBinary,
    IrBlock,
    IrCall,
    IrCase,
    IrCaseClause,
    IrDelay,
    IrExprStmt,
    IrFuncDef,
    IrImport,
    IrLambda,
    IrList,
    IrLiteral,
    IrMap,
    IrNode,
    IrOptionNone,
    IrOptionSome,
    IrPattern,
    IrPatBind,
    IrPatGlob,
    IrPatList,
    IrPatLiteral,
    IrPatMap,
    IrPatNone,
    IrPatRest,
    IrPatSome,
    IrPatTuple,
    IrPatWildcard,
    IrPipeline,
    IrQuote,
    IrQuasiQuote,
    IrSpread,
    IrUnary,
    IrUnquote,
    IrUnquoteSplicing,
    IrVar,
    ListLiteral,
    MapLiteral,
    Number,
    String,
    Var,
    assert_portable_core_ir,
)


def normalize_portable_ir(nodes: Iterable[IrNode]) -> list[dict[str, Any]]:
    lowered = list(nodes)
    assert_portable_core_ir(lowered)
    return [_normalize_ir_node(node) for node in lowered]


def _normalize_ir_node(node: IrNode) -> dict[str, Any]:
    if isinstance(node, IrAnnotation):
        return {
            "node": "IrAnnotation",
            "name": node.name,
            "value": _normalize_ir_node(node.value),
        }
    if isinstance(node, IrLiteral):
        return {
            "node": "IrLiteral",
            "value": node.value,
        }
    if isinstance(node, IrOptionNone):
        return {
            "node": "IrOptionNone",
            "reason": None if node.reason is None else _normalize_ir_node(node.reason),
            "context": None if node.context is None else _normalize_ir_node(node.context),
        }
    if isinstance(node, IrOptionSome):
        return {
            "node": "IrOptionSome",
            "value": _normalize_ir_node(node.value),
        }
    if isinstance(node, IrVar):
        return {
            "node": "IrVar",
            "name": node.name,
        }
    if isinstance(node, IrQuote):
        return {
            "node": "IrQuote",
            "expr": _normalize_quoted_syntax(node.expr),
        }
    if isinstance(node, IrDelay):
        return {
            "node": "IrDelay",
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrQuasiQuote):
        return {
            "node": "IrQuasiQuote",
            "expr": _normalize_quoted_syntax(node.expr),
        }
    if isinstance(node, IrUnquote):
        return {
            "node": "IrUnquote",
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrUnquoteSplicing):
        return {
            "node": "IrUnquoteSplicing",
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrUnary):
        return {
            "node": "IrUnary",
            "op": node.op,
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrBinary):
        return {
            "node": "IrBinary",
            "left": _normalize_ir_node(node.left),
            "op": node.op,
            "right": _normalize_ir_node(node.right),
        }
    if isinstance(node, IrPipeline):
        return {
            "node": "IrPipeline",
            "source": _normalize_ir_node(node.source),
            "stages": [_normalize_ir_node(stage) for stage in node.stages],
        }
    if isinstance(node, IrCall):
        return {
            "node": "IrCall",
            "fn": _normalize_ir_node(node.fn),
            "args": [_normalize_ir_node(arg) for arg in node.args],
        }
    if isinstance(node, IrExprStmt):
        return {
            "node": "IrExprStmt",
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrBlock):
        return {
            "node": "IrBlock",
            "exprs": [_normalize_ir_node(expr) for expr in node.exprs],
        }
    if isinstance(node, IrList):
        return {
            "node": "IrList",
            "items": [_normalize_ir_node(item) for item in node.items],
        }
    if isinstance(node, IrMap):
        return {
            "node": "IrMap",
            "items": [
                {
                    "key": key,
                    "value": _normalize_ir_node(value),
                }
                for key, value in node.items
            ],
        }
    if isinstance(node, IrSpread):
        return {
            "node": "IrSpread",
            "expr": _normalize_ir_node(node.expr),
        }
    if isinstance(node, IrCaseClause):
        normalized = {
            "node": "IrCaseClause",
            "pattern": _normalize_pattern(node.pattern),
            "result": _normalize_ir_node(node.result),
        }
        if node.guard is not None:
            normalized["guard"] = _normalize_ir_node(node.guard)
        return normalized
    if isinstance(node, IrCase):
        return {
            "node": "IrCase",
            "clauses": [_normalize_ir_node(clause) for clause in node.clauses],
        }
    if isinstance(node, IrLambda):
        normalized = {
            "node": "IrLambda",
            "params": list(node.params),
            "body": _normalize_ir_node(node.body),
        }
        if node.rest_param is not None:
            normalized["rest_param"] = node.rest_param
        return normalized
    if isinstance(node, IrAssign):
        normalized = {
            "node": "IrAssign",
            "name": node.name,
            "expr": _normalize_ir_node(node.expr),
        }
        if node.annotations:
            normalized["annotations"] = [_normalize_ir_node(annotation) for annotation in node.annotations]
        return normalized
    if isinstance(node, IrFuncDef):
        normalized = {
            "node": "IrFuncDef",
            "name": node.name,
            "params": list(node.params),
            "body": _normalize_ir_node(node.body),
        }
        if node.rest_param is not None:
            normalized["rest_param"] = node.rest_param
        if node.docstring is not None:
            normalized["docstring"] = node.docstring
        if node.annotations:
            normalized["annotations"] = [_normalize_ir_node(annotation) for annotation in node.annotations]
        return normalized
    if isinstance(node, IrImport):
        normalized = {
            "node": "IrImport",
            "module_name": node.module_name,
        }
        if node.alias is not None:
            normalized["alias"] = node.alias
        return normalized

    raise TypeError(
        "Portable Core IR normalization failed: unsupported node "
        f"{type(node).__name__} in shared IR path."
    )


def _normalize_pattern(pattern: IrPattern) -> dict[str, Any]:
    if isinstance(pattern, IrPatLiteral):
        return {
            "node": "IrPatLiteral",
            "value": pattern.value,
        }
    if isinstance(pattern, IrPatBind):
        return {
            "node": "IrPatBind",
            "name": pattern.name,
        }
    if isinstance(pattern, IrPatWildcard):
        return {"node": "IrPatWildcard"}
    if isinstance(pattern, IrPatRest):
        return {
            "node": "IrPatRest",
            "name": pattern.name,
        }
    if isinstance(pattern, IrPatTuple):
        return {
            "node": "IrPatTuple",
            "items": [_normalize_pattern(item) for item in pattern.items],
        }
    if isinstance(pattern, IrPatList):
        return {
            "node": "IrPatList",
            "items": [_normalize_pattern(item) for item in pattern.items],
        }
    if isinstance(pattern, IrPatMap):
        return {
            "node": "IrPatMap",
            "items": [
                {
                    "key": key,
                    "value": _normalize_pattern(value),
                }
                for key, value in pattern.items
            ],
        }
    if isinstance(pattern, IrPatGlob):
        return {
            "node": "IrPatGlob",
            "pattern": pattern.matcher.source,
        }
    if isinstance(pattern, IrPatSome):
        return {
            "node": "IrPatSome",
            "inner": _normalize_pattern(pattern.inner),
        }
    if isinstance(pattern, IrPatNone):
        return {
            "node": "IrPatNone",
            "reason": None if pattern.reason is None else _normalize_pattern(pattern.reason),
            "context": None if pattern.context is None else _normalize_pattern(pattern.context),
        }

    raise TypeError(
        "Portable Core IR normalization failed: unsupported pattern "
        f"{type(pattern).__name__} in shared IR path."
    )


def _normalize_quoted_syntax(expr: Any) -> dict[str, Any]:
    if isinstance(expr, String):
        return {"kind": "Literal", "value": expr.value}
    if isinstance(expr, Number):
        return {"kind": "Literal", "value": expr.value}
    if isinstance(expr, Boolean):
        return {"kind": "Literal", "value": expr.value}
    if isinstance(expr, Var):
        return {"kind": "Var", "name": expr.name}
    if isinstance(expr, ListLiteral):
        return {
            "kind": "List",
            "items": [_normalize_quoted_syntax(item) for item in expr.items],
        }
    if isinstance(expr, MapLiteral):
        return {
            "kind": "Map",
            "items": [
                {
                    "key": _normalize_quoted_map_key(key),
                    "value": _normalize_quoted_syntax(value),
                }
                for key, value in expr.items
            ],
        }

    raise TypeError(
        "Portable Core IR normalization failed: unsupported quoted syntax "
        f"{type(expr).__name__} in shared IR path."
    )


def _normalize_quoted_map_key(key: Any) -> str:
    if isinstance(key, Var):
        return key.name
    if isinstance(key, String):
        return key.value

    raise TypeError(
        "Portable Core IR normalization failed: unsupported quoted map key "
        f"{type(key).__name__} in shared IR path."
    )
