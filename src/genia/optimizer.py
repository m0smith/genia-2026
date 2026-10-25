"""Python-host post-lowering optimizations and conservative recursive-call analysis."""
from __future__ import annotations

from typing import Iterable

if __package__ in (None, ""):
    from genia.ir import (
        IrBinary,
        IrCall,
        IrCase,
        IrCaseClause,
        IrFuncDef,
        IrListTraversalLoop,
        IrLiteral,
        IrNode,
        IrOptionNone,
        IrVar,
    )
    from genia.pattern_match import (
        IrPatBind,
        IrPatList,
        IrPatLiteral,
        IrPatRest,
        IrPatTuple,
    )
    from genia.numeric_source import numeric_literal_runtime_value
else:
    from .ir import (
        IrBinary,
        IrCall,
        IrCase,
        IrCaseClause,
        IrFuncDef,
        IrListTraversalLoop,
        IrLiteral,
        IrNode,
        IrOptionNone,
        IrVar,
    )
    from .pattern_match import (
        IrPatBind,
        IrPatList,
        IrPatLiteral,
        IrPatRest,
        IrPatTuple,
    )
    from .numeric_source import numeric_literal_runtime_value


def _is_integer_literal_one(value: object) -> bool:
    """True when an IrLiteral value denotes the Integer literal 1.

    Handles both the R21 E21-2 tagged payload shape and (defensively) a
    bare numeric value, without introducing any new numeric comparison
    semantics beyond this existing tail-recursion-shape detection.
    """
    if isinstance(value, dict):
        return numeric_literal_runtime_value(value) == 1
    return value == 1


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
    """Rewrite a recognized nth-style list recursion to `IrListTraversalLoop`, else return `fn`.

    The rewrite keeps the original grouped case on the node so evaluation can fall back to it.
    """
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
        and _is_integer_literal_one(n_arg.right.value)
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
            case=case,
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
    """Count syntactic calls across IR children, including new and R20 records.

    Quoted syntax is not executable IR. This is a conservative shape check,
    not a scope-aware call-graph analysis or a declaration-reordering pass.
    Calls inside list/map values also count: an extra recursive case arm must
    prevent the nth-style rewrite from discarding that arm. This deliberately
    narrows eligibility compared with the old incomplete child traversal.
    """
    from .ir import iter_ir_nodes
    return sum(isinstance(child, IrCall) and isinstance(child.fn, IrVar)
               and child.fn.name == fn_name for child in iter_ir_nodes(node))
