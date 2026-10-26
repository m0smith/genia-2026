"""Slice C GREEN repair R1 (#1269, PR #1270): optimizer rewrite must be semantics-preserving.

PYTHON REFERENCE HOST ONLY. Codex counterexamples A/B/C: the nth-style rewrite
may be admitted only for the exact canonical clause shape in canonical order;
every other program must run its original ordered clauses unchanged.
Each program is run optimizer-off and optimizer-on and compared on stdout,
value and error text.
"""

from __future__ import annotations

import pytest

from genia import ir
from genia.evaluator import Evaluator
from genia.interpreter import Parser, lex, lower_program
from genia.optimizer import optimize_program
from genia.utf8 import format_debug
from tests.unit.model_b_slice_c_support import fresh_env


def _run(source: str, *, optimize: bool):
    env, printed = fresh_env()
    try:
        nodes = lower_program(Parser(lex(source), source=source, filename="<command>").parse_program())
        if optimize:
            nodes = optimize_program(nodes)
        value = Evaluator(env).eval_program(nodes)
    except Exception as error:  # noqa: BLE001 - observable error text is the datum
        return "".join(printed), f"Error: {error}"
    return "".join(printed), "" if value is None else format_debug(value)


def _rewritten(source: str) -> bool:
    nodes = optimize_program(lower_program(Parser(lex(source), source=source, filename="<command>").parse_program()))
    return any(isinstance(getattr(n, "body", None), ir.IrListTraversalLoop) for n in nodes)


CANONICAL = "pick(n, xs) = (_, []) -> nil | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"

COUNTER_A = (
    'pick(n, xs) = (1, [x, .._]) -> { print("effect"); 99 } | (_, []) -> nil '
    "| (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
    "pick(1, [7, 8])"
)
COUNTER_B = (
    "pick(n, xs) = (_, []) -> nil | (n, [_, ..rest]) -> pick(n - 1, rest) "
    "| (0, [x, .._]) -> x\n"
    "pick(0, [7])"
)
COUNTER_C = (
    "pick(n, xs) = (0, []) -> nil | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
    "pick(2, [7])"
)


@pytest.mark.parametrize("name,source", [("A", COUNTER_A), ("B", COUNTER_B), ("C", COUNTER_C)])
def test_counterexample_matches_unoptimized_execution(name, source):
    assert _run(source, optimize=True) == _run(source, optimize=False)


def test_counterexample_a_keeps_earlier_arm_effect():
    assert _run(COUNTER_A, optimize=True) == ("effect\n", "99")


def test_counterexample_b_keeps_clause_order():
    assert _run(COUNTER_B, optimize=True) == _run(COUNTER_B, optimize=False)
    assert _run(COUNTER_B, optimize=True)[1] != "7"


def test_counterexample_c_keeps_unconstrained_empty_arm_requirement():
    out = _run(COUNTER_C, optimize=True)
    assert out[1].startswith("Error: No matching case for function pick/2")
    assert out == _run(COUNTER_C, optimize=False)


@pytest.mark.parametrize("source", [COUNTER_A, COUNTER_B, COUNTER_C])
def test_non_canonical_shapes_are_not_admitted(source):
    assert not _rewritten(source)


@pytest.mark.parametrize("call", ["pick(0, [7])", "pick(2, [7, 8, 9])", "pick(5, [1])", "pick(0, [])"])
def test_canonical_shape_still_rewritten_and_equivalent(call):
    source = CANONICAL + call
    assert _rewritten(source)
    assert _run(source, optimize=True) == _run(source, optimize=False)
