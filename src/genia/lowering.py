from __future__ import annotations

from typing import Iterable

if __package__ in (None, ""):
    from genia.ast_nodes import (
        AnnotatedNode,
        Annotation,
        Assign,
        Binary,
        Block,
        Boolean,
        Call,
        CaseExpr,
        Delay,
        ExprStmt,
        FuncDef,
        GlobPattern,
        ImportStmt,
        Lambda,
        ListLiteral,
        ListPattern,
        MapLiteral,
        MapPattern,
        Nil,
        Node,
        NoneOption,
        Number,
        QuasiQuote,
        Quote,
        RestPattern,
        ShellStage,
        SomePattern,
        Spread,
        String,
        SymbolLiteral,
        TuplePattern,
        Unary,
        Unquote,
        UnquoteSplicing,
        Var,
        WildcardPattern,
    )
    from genia.ir import (
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
        IrPipeline,
        IrQuote,
        IrQuasiQuote,
        IrShellStage,
        IrSpread,
        IrUnary,
        IrUnquote,
        IrUnquoteSplicing,
        IrVar,
    )
    from genia.pattern_match import (
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
        IrPattern,
        compile_glob_pattern,
    )
    from genia.values import symbol
else:
    from .ast_nodes import (
        AnnotatedNode,
        Annotation,
        Assign,
        Binary,
        Block,
        Boolean,
        Call,
        CaseExpr,
        Delay,
        ExprStmt,
        FuncDef,
        GlobPattern,
        ImportStmt,
        Lambda,
        ListLiteral,
        ListPattern,
        MapLiteral,
        MapPattern,
        Nil,
        Node,
        NoneOption,
        Number,
        QuasiQuote,
        Quote,
        RestPattern,
        ShellStage,
        SomePattern,
        Spread,
        String,
        SymbolLiteral,
        TuplePattern,
        Unary,
        Unquote,
        UnquoteSplicing,
        Var,
        WildcardPattern,
    )
    from .ir import (
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
        IrPipeline,
        IrQuote,
        IrQuasiQuote,
        IrShellStage,
        IrSpread,
        IrUnary,
        IrUnquote,
        IrUnquoteSplicing,
        IrVar,
    )
    from .pattern_match import (
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
        IrPattern,
        compile_glob_pattern,
    )
    from .values import symbol


def lower_program(nodes: Iterable[Node]) -> list[IrNode]:
    return [lower_node(node) for node in nodes]


def _lower_annotations(annotations: list[Annotation]) -> list[IrAnnotation]:
    return [IrAnnotation(annotation.name, lower_node(annotation.value), span=annotation.span) for annotation in annotations]


def _map_literal_key_name(key: Node) -> str:
    if isinstance(key, Var):
        return key.name
    if isinstance(key, String):
        return key.value
    raise RuntimeError(f"Unsupported map literal key node: {key!r}")


def _flatten_pipeline_ast(node: Node) -> tuple[Node, list[Node]]:
    if isinstance(node, Binary) and node.op == "PIPE_FWD":
        source, stages = _flatten_pipeline_ast(node.left)
        return source, [*stages, node.right]
    return node, []


def lower_node(node: Node) -> IrNode:
    if isinstance(node, AnnotatedNode):
        lowered_annotations = _lower_annotations(node.annotations)
        target = node.target
        if isinstance(target, Assign):
            return IrAssign(target.name, lower_node(target.expr), annotations=lowered_annotations, span=node.span)
        if isinstance(target, FuncDef):
            return IrFuncDef(
                target.name,
                target.params,
                target.rest_param,
                target.docstring,
                lower_node(target.body),
                annotations=lowered_annotations,
                span=node.span,
            )
        raise RuntimeError(f"Annotated target is not bindable during lowering: {target!r}")
    if isinstance(node, ExprStmt):
        return IrExprStmt(lower_node(node.expr), span=node.span)
    if isinstance(node, Number):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, String):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Boolean):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Nil):
        return IrOptionNone(IrLiteral("nil", span=node.span), None, span=node.span)
    if isinstance(node, NoneOption):
        reason = IrQuote(node.reason, span=node.reason.span) if node.reason is not None else None
        context = lower_node(node.context) if node.context is not None else None
        return IrOptionNone(reason, context, span=node.span)
    if isinstance(node, SymbolLiteral):
        return IrLiteral(symbol(node.name), span=node.span)
    if isinstance(node, Var):
        return IrVar(node.name, span=node.span)
    if isinstance(node, Quote):
        return IrQuote(node.expr, span=node.span)
    if isinstance(node, Delay):
        return IrDelay(lower_node(node.expr), span=node.span)
    if isinstance(node, QuasiQuote):
        return IrQuasiQuote(node.expr, span=node.span)
    if isinstance(node, Unquote):
        return IrUnquote(lower_node(node.expr), span=node.span)
    if isinstance(node, UnquoteSplicing):
        return IrUnquoteSplicing(lower_node(node.expr), span=node.span)
    if isinstance(node, Unary):
        return IrUnary(node.op, lower_node(node.expr), span=node.span)
    if isinstance(node, Binary):
        if node.op == "PIPE_FWD":
            source, stages = _flatten_pipeline_ast(node)
            return IrPipeline(lower_node(source), [lower_node(stage) for stage in stages], span=node.span)
        return IrBinary(lower_node(node.left), node.op, lower_node(node.right), span=node.span)
    if isinstance(node, Call):
        if isinstance(node.fn, Var) and node.fn.name == "some" and len(node.args) == 1:
            return IrOptionSome(lower_node(node.args[0]), span=node.span)
        return IrCall(lower_node(node.fn), [lower_node(arg) for arg in node.args], span=node.span)
    if isinstance(node, Block):
        return IrBlock([lower_node(expr) for expr in node.exprs], span=node.span)
    if isinstance(node, ListLiteral):
        return IrList([lower_node(item) for item in node.items], span=node.span)
    if isinstance(node, MapLiteral):
        return IrMap([(_map_literal_key_name(key), lower_node(value)) for key, value in node.items], span=node.span)
    if isinstance(node, Spread):
        return IrSpread(lower_node(node.expr), span=node.span)
    if isinstance(node, CaseExpr):
        return IrCase(
            [
                IrCaseClause(
                    lower_pattern(clause.pattern),
                    lower_node(clause.guard) if clause.guard is not None else None,
                    lower_node(clause.result),
                    span=clause.span,
                )
                for clause in node.clauses
            ],
            span=node.span,
        )
    if isinstance(node, Lambda):
        pattern = node.pattern
        if pattern is not None and _lambda_pattern_is_simple_parameter_shape(pattern, node.params, node.rest_param):
            pattern = None
        if pattern is None:
            items: list[Node] = [Var(name) for name in node.params]
            if node.rest_param is not None:
                items.append(RestPattern(node.rest_param))
            pattern = TuplePattern(items, span=node.span)
            lowered_pattern = None
        else:
            lowered_pattern = lower_pattern(pattern)
        return IrLambda(
            node.params,
            node.rest_param,
            lower_node(node.body),
            span=node.span,
            pattern=lowered_pattern,
        )
    if isinstance(node, Assign):
        return IrAssign(node.name, lower_node(node.expr), span=node.span)
    if isinstance(node, FuncDef):
        return IrFuncDef(
            node.name,
            node.params,
            node.rest_param,
            node.docstring,
            lower_node(node.body),
            annotations=[],
            span=node.span,
        )
    if isinstance(node, ImportStmt):
        return IrImport(node.module_name, node.alias, span=node.span)
    if isinstance(node, ShellStage):
        return IrShellStage(node.command, span=node.span)
    raise RuntimeError(f"Unknown AST node during lowering: {node!r}")


def lower_pattern(pattern: Node) -> IrPattern:
    if isinstance(pattern, Number):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, String):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, Boolean):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, Nil):
        return IrPatNone(IrPatLiteral("nil"), None)
    if isinstance(pattern, NoneOption):
        return IrPatNone(
            lower_pattern(pattern.reason) if pattern.reason is not None else None,
            lower_pattern(pattern.context) if pattern.context is not None else None,
        )
    if isinstance(pattern, SymbolLiteral):
        return IrPatLiteral(symbol(pattern.name))
    if isinstance(pattern, WildcardPattern):
        return IrPatWildcard()
    if isinstance(pattern, RestPattern):
        return IrPatRest(pattern.name)
    if isinstance(pattern, Var):
        return IrPatBind(pattern.name)
    if isinstance(pattern, TuplePattern):
        return IrPatTuple([lower_pattern(item) for item in pattern.items])
    if isinstance(pattern, ListPattern):
        return IrPatList([lower_pattern(item) for item in pattern.items])
    if isinstance(pattern, MapPattern):
        return IrPatMap([(key, lower_pattern(value)) for key, value in pattern.items])
    if isinstance(pattern, GlobPattern):
        return IrPatGlob(compile_glob_pattern(pattern.pattern))
    if isinstance(pattern, SomePattern):
        return IrPatSome(lower_pattern(pattern.inner))
    raise RuntimeError(f"Unknown pattern during lowering: {pattern!r}")


def _lambda_pattern_is_simple_parameter_shape(
    pattern: Node,
    params: list[str],
    rest_param: str | None,
) -> bool:
    if not isinstance(pattern, TuplePattern):
        return False
    fixed_items = pattern.items
    rest_item: Node | None = None
    if fixed_items and isinstance(fixed_items[-1], RestPattern):
        rest_item = fixed_items[-1]
        fixed_items = fixed_items[:-1]
    if len(fixed_items) != len(params):
        return False
    if any(not isinstance(item, Var) for item in fixed_items):
        return False
    if [item.name for item in fixed_items if isinstance(item, Var)] != params:
        return False
    if rest_item is None:
        return rest_param is None
    return isinstance(rest_item, RestPattern) and rest_item.name == rest_param
