from __future__ import annotations

from typing import Iterable

if __package__ in (None, ""):
    from genia.ir import (
        IrAssign,
        IrBinary,
        IrBlock,
        IrCall,
        IrCase,
        IrCaseClause,
        IrExprStmt,
        IrFuncDef,
        IrLambda,
        IrListTraversalLoop,
        IrLiteral,
        IrNode,
        IrOptionNone,
        IrOptionSome,
        IrPipeline,
        IrUnary,
        IrVar,
    )
    from genia.pattern_match import (
        IrPatBind,
        IrPatList,
        IrPatLiteral,
        IrPatRest,
        IrPatTuple,
    )
else:
    from .ir import (
        IrAssign,
        IrBinary,
        IrBlock,
        IrCall,
        IrCase,
        IrCaseClause,
        IrExprStmt,
        IrFuncDef,
        IrLambda,
        IrListTraversalLoop,
        IrLiteral,
        IrNode,
        IrOptionNone,
        IrOptionSome,
        IrPipeline,
        IrUnary,
        IrVar,
    )
    from .pattern_match import (
        IrPatBind,
        IrPatList,
        IrPatLiteral,
        IrPatRest,
        IrPatTuple,
    )


def optimize_program(ir_nodes: Iterable[IrNode], *, debug: bool = False) -> list[IrNode]:
    optimized: list[IrNode] = []
    for node in ir_nodes:
        if isinstance(node, IrFuncDef):
            rewritten = optimize_nth_style_recursion(node)
            if rewritten is not node and debug:
                print(f"Applied list traversal optimization to function {node.name}/{len(node.params)}")
            optimized.append(rewritten)
        else:
            optimized.append(node)
    return optimized


def optimize_nth_style_recursion(fn: IrFuncDef) -> IrFuncDef:
    if fn.rest_param is not None or len(fn.params) != 2 or not isinstance(fn.body, IrCase):
        return fn
    case = fn.body
    if any(clause.guard is not None for clause in case.clauses):
        return fn

    empty_clause: IrCaseClause | None = None
    zero_clause: IrCaseClause | None = None
    recur_clause: IrCaseClause | None = None

    for clause in case.clauses:
        if recursive_call_count(clause.result, fn.name) > 1:
            return fn
        tuple_pat = clause.pattern
        if not isinstance(tuple_pat, IrPatTuple) or len(tuple_pat.items) != 2:
            continue
        n_pat, xs_pat = tuple_pat.items
        if (
            isinstance(xs_pat, IrPatList)
            and len(xs_pat.items) == 0
            and (
                (isinstance(clause.result, IrLiteral) and clause.result.value is None)
                or (
                    isinstance(clause.result, IrOptionNone)
                    and isinstance(clause.result.reason, IrLiteral)
                    and clause.result.reason.value == "nil"
                    and clause.result.context is None
                )
            )
            and empty_clause is None
        ):
            empty_clause = clause
            continue
        if (
            isinstance(n_pat, IrPatLiteral)
            and n_pat.value == 0
            and isinstance(xs_pat, IrPatList)
            and len(xs_pat.items) == 2
            and isinstance(xs_pat.items[0], IrPatBind)
            and isinstance(xs_pat.items[1], IrPatRest)
            and isinstance(clause.result, IrVar)
            and clause.result.name == xs_pat.items[0].name
            and zero_clause is None
        ):
            zero_clause = clause
            continue
        if recur_clause is None and is_tail_recursive_step(clause, fn.name):
            recur_clause = clause
            n_bind = n_pat if isinstance(n_pat, IrPatBind) else None
            rest_pat = xs_pat.items[1] if isinstance(xs_pat, IrPatList) and len(xs_pat.items) == 2 else None
            if n_bind is None or not isinstance(rest_pat, IrPatRest) or rest_pat.name is None:
                return fn
            continue
        if recursive_call_count(clause.result, fn.name) > 0:
            return fn

    if empty_clause is None or zero_clause is None or recur_clause is None:
        return fn
    recur_pat = recur_clause.pattern
    assert isinstance(recur_pat, IrPatTuple)
    recur_n_pat, recur_xs_pat = recur_pat.items
    if not (isinstance(recur_n_pat, IrPatBind) and isinstance(recur_xs_pat, IrPatList)):
        return fn
    if len(recur_xs_pat.items) != 2 or not isinstance(recur_xs_pat.items[1], IrPatRest):
        return fn
    rest_name = recur_xs_pat.items[1].name
    if rest_name is None:
        return fn
    recur_result = recur_clause.result
    if not isinstance(recur_result, IrCall) or not isinstance(recur_result.fn, IrVar) or recur_result.fn.name != fn.name:
        return fn
    if len(recur_result.args) != 2:
        return fn
    n_arg, xs_arg = recur_result.args
    if not (
        isinstance(n_arg, IrBinary)
        and n_arg.op == "MINUS"
        and isinstance(n_arg.left, IrVar)
        and n_arg.left.name == recur_n_pat.name
        and isinstance(n_arg.right, IrLiteral)
        and n_arg.right.value == 1
    ):
        return fn
    if not (isinstance(xs_arg, IrVar) and xs_arg.name == rest_name):
        return fn

    return IrFuncDef(
        fn.name,
        fn.params,
        fn.rest_param,
        fn.docstring,
        IrListTraversalLoop(
            counter_var=fn.params[0],
            list_var=fn.params[1],
            step_size=1,
            empty_clause=empty_clause,
            zero_clause=zero_clause,
            span=fn.span,
        ),
        annotations=fn.annotations,
        span=fn.span,
    )


def is_tail_recursive_step(clause: IrCaseClause, fn_name: str) -> bool:
    tuple_pat = clause.pattern
    if not isinstance(tuple_pat, IrPatTuple) or len(tuple_pat.items) != 2:
        return False
    _, xs_pat = tuple_pat.items
    if not (isinstance(xs_pat, IrPatList) and len(xs_pat.items) == 2 and isinstance(xs_pat.items[1], IrPatRest)):
        return False
    result = clause.result
    if not isinstance(result, IrCall):
        return False
    if not isinstance(result.fn, IrVar) or result.fn.name != fn_name:
        return False
    return recursive_call_count(result, fn_name) == 1


def recursive_call_count(node: IrNode, fn_name: str) -> int:
    if isinstance(node, IrCall):
        own = 1 if isinstance(node.fn, IrVar) and node.fn.name == fn_name else 0
        return own + recursive_call_count(node.fn, fn_name) + sum(recursive_call_count(arg, fn_name) for arg in node.args)
    if isinstance(node, IrPipeline):
        return recursive_call_count(node.source, fn_name) + sum(recursive_call_count(stage, fn_name) for stage in node.stages)
    if isinstance(node, IrOptionSome):
        return recursive_call_count(node.value, fn_name)
    if isinstance(node, IrOptionNone):
        return (
            recursive_call_count(node.reason, fn_name) if node.reason is not None else 0
        ) + (
            recursive_call_count(node.context, fn_name) if node.context is not None else 0
        )
    if isinstance(node, IrUnary):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrBinary):
        return recursive_call_count(node.left, fn_name) + recursive_call_count(node.right, fn_name)
    if isinstance(node, IrBlock):
        return sum(recursive_call_count(expr, fn_name) for expr in node.exprs)
    if isinstance(node, IrExprStmt):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrCase):
        return sum(recursive_call_count(clause.result, fn_name) for clause in node.clauses)
    if isinstance(node, IrAssign):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrLambda):
        return recursive_call_count(node.body, fn_name)
    return 0
