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


# --- R1-A: recursive-arm pattern constraints (Codex review 5669388186) -----------------------

TAIL = "pick(n - 1, rest)"


def _pick(recur_pattern: str, call: str, tail: str = TAIL) -> str:
    return (
        "pick(n, xs) = (_, []) -> nil | (0, [x, .._]) -> x | "
        f"{recur_pattern} -> {tail}\n{call}"
    )


CONSTRAINED_RECURSIVE = [
    pytest.param(_pick("(n, [1, ..rest])", "pick(1, [7, 8])"), id="constant-head"),
    pytest.param(_pick("(n, [n, ..rest])", "pick(1, [7, 8])"), id="repeated-counter-head"),
    pytest.param(_pick("(n, [n, ..rest])", "pick(1, [1, 8])"), id="repeated-counter-head-matching"),
    pytest.param(_pick("(n, [_, ..n])", "pick(1, [7, 8])", "pick(1, n)"), id="rest-repeats-counter"),
    pytest.param(_pick("(n, [[], ..rest])", "pick(1, [[], 8])"), id="nested-list-head"),
    pytest.param(_pick("(n, [h, ..h])", "pick(1, [7, 8])", "pick(n - 1, h)"), id="head-repeats-rest"),
    pytest.param(_pick("(5, [_, ..rest])", "pick(1, [7, 8])"), id="constant-counter"),
]


@pytest.mark.parametrize("source", CONSTRAINED_RECURSIVE)
def test_constrained_recursive_arm_is_equivalent_and_not_admitted(source):
    assert _run(source, optimize=True) == _run(source, optimize=False)
    assert not _rewritten(source)


def test_constrained_recursive_head_keeps_the_grouped_miss():
    out = _run(_pick("(n, [1, ..rest])", "pick(1, [7, 8])"), optimize=True)
    assert out[1].startswith("Error: No matching case for function pick/2 with arguments [1, [7, 8]]")


@pytest.mark.parametrize("head", ["_", "h", "other"])
def test_unconstrained_recursive_head_stays_admitted(head):
    source = _pick(f"(n, [{head}, ..rest])", "pick(1, [7, 8])")
    assert _rewritten(source)
    assert _run(source, optimize=True) == _run(source, optimize=False) == ("", "8")


# --- R1-B: recursive callee resolution -------------------------------------------------------

REBIND = CANONICAL + "alias = pick\npick = (n, xs) -> 99\nalias(1, [7, 8])"
SHADOW = _pick("(n, [_, ..pick])", "pick(1, [7, 8])", "pick(n - 1, pick)")
PARAM_SHADOW = (
    "pick(pick, xs) = (_, []) -> nil | (0, [x, .._]) -> x | (pick, [_, ..rest]) -> pick(pick - 1, rest)\n"
    "pick(1, [7, 8])"
)
EARLIER_CLAUSE = (
    "pick(1, [_, .._]) = 55\n" + CANONICAL + "pick(2, [7, 8, 9])"
)


def test_rebinding_resolves_the_current_callee():
    on, off = _run(REBIND, optimize=True), _run(REBIND, optimize=False)
    assert on == off == ("", "99")
    assert _rewritten(REBIND)  # still admitted: correctness comes from runtime resolution


def test_local_rest_binder_shadowing_the_callee_is_not_admitted():
    on, off = _run(SHADOW, optimize=True), _run(SHADOW, optimize=False)
    assert on == off
    assert "callable" in on[1]
    assert not _rewritten(SHADOW)


def test_parameter_shadowing_the_callee_is_not_admitted():
    assert _run(PARAM_SHADOW, optimize=True) == _run(PARAM_SHADOW, optimize=False)
    assert not _rewritten(PARAM_SHADOW)


def test_recursive_call_dispatches_through_the_whole_group():
    on, off = _run(EARLIER_CLAUSE, optimize=True), _run(EARLIER_CLAUSE, optimize=False)
    assert on == off == ("", "55")


def test_canonical_fast_path_still_taken_when_binding_is_stable():
    assert _rewritten(CANONICAL)
    assert _run(CANONICAL + "pick(1, [7, 8])", optimize=True) == ("", "8")


def test_canonical_fast_path_does_not_fall_back_to_the_retained_case(monkeypatch):
    """Non-vacuity: a stable canonical program must not reach the ordered-case evaluator."""
    def no_case(self, *args, **kwargs):
        raise AssertionError("retained case evaluated on the canonical fast path")

    monkeypatch.setattr(Evaluator, "eval_case_expr", no_case)
    assert _run(CANONICAL + "pick(1, [7, 8])", optimize=True) == ("", "8")


def test_rebound_callee_does_reach_the_retained_case(monkeypatch):
    reached = []
    original = Evaluator.eval_case_expr

    def spy(self, *args, **kwargs):
        reached.append(True)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Evaluator, "eval_case_expr", spy)
    assert _run(REBIND, optimize=True) == ("", "99")
    assert reached
