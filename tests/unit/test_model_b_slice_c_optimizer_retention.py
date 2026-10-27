"""Slice C RED host-local tests: optimizer rewrite participation and arm retention (HL-8).

PYTHON REFERENCE HOST ONLY (issue #1269; test plan C-OPTIM, C-D8, R6.E HL-8;
pre-flight 2.6 invariant 4). The shared ``model-b-c-optim-*`` cases use ``0`` as
the empty-arm result so that C++ can run them; ``optimize_nth_style_recursion``
only rewrites an empty arm that returns ``nil``/``none("nil")``, so those
shared witnesses never reach the rewrite. Every program below that is meant to
exercise the rewrite therefore uses ``nil``, and each test first proves the
rewrite really ran (or was declined) by inspecting lowered versus optimized IR.

What the approved design requires (D8, invariant 4): the original grouped-body
arm keys, ordinals, guards and provenance of an ordinary declaration are
retained or losslessly derivable from the *unoptimized* semantic structure and
equal the unoptimized ones. The optimizer's ``IrListTraversalLoop`` keeps only
``empty_clause`` and ``zero_clause`` (plus counters), so the recursive arm is
absent from the optimized declaration. Tests that state the retention
requirement therefore FAIL at RED. The optimizer is not changed here.

``*_today`` tests pin existing behavior and pass; the others state approved
behavior and fail until GREEN. The retention boundary is deliberately the whole
optimized program (any reachable ``IrCaseClause``), not a new field name:
GREEN may keep the arms on a declaration record, on the node, or elsewhere in
the program, as long as the original structure stays reachable and equal.
"""

from __future__ import annotations

from typing import Any

import pytest

from genia import ir
from genia.evaluator import Evaluator
from genia.interpreter import Parser, lex, lower_program
from genia.optimizer import optimize_program
from genia.utf8 import format_debug
from tests.unit.model_b_slice_c_support import dispatch_key, fresh_env, reachable_case_clauses

NIL_PICK = (
    "pick(n, xs) = (_, []) -> nil | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
)
ZERO_PICK = NIL_PICK.replace("-> nil", "-> 0")  # the frozen shared-case spelling


def _lowered(source: str):
    return lower_program(Parser(lex(source), source=source, filename="<command>").parse_program())


def _clauses(root: Any) -> list[ir.IrCaseClause]:
    """Every IrCaseClause reachable from the program (A3 retention boundary lives in the support module)."""
    return reachable_case_clauses(root)


def _arm_record(ordinal: int, clause: ir.IrCaseClause) -> tuple:
    """Ordinal, span-free arm key, guard presence and provenance of one grouped arm."""
    return (ordinal, dispatch_key(clause.pattern, clause.guard), clause.guard is not None, clause.span)


def _arms(program: Any) -> list[tuple]:
    return [_arm_record(i, c) for i, c in enumerate(_clauses(program))]


def _run(source: str, *, optimize: bool) -> tuple[str, str, int]:
    env, printed = fresh_env()
    try:
        nodes = _lowered(source)
        if optimize:
            nodes = optimize_program(nodes)
        value = Evaluator(env).eval_program(nodes)
    except Exception as error:  # noqa: BLE001 - observable error text is the datum
        return "".join(printed), f"Error: {error}\n", 1
    shown = "" if value is None else format_debug(value) + "\n"
    return "".join(printed) + shown, "", 0


# --- rewrite participation (non-vacuity) -----------------------------------------------------


def test_nil_empty_arm_reaches_the_nth_style_rewrite_today():
    lowered = _lowered(NIL_PICK)
    optimized = optimize_program(lowered)
    assert isinstance(lowered[0].body, ir.IrCase) and len(lowered[0].body.clauses) == 3
    assert isinstance(optimized[0].body, ir.IrListTraversalLoop)
    assert optimized[0] is not lowered[0]
    loop = optimized[0].body
    original = lowered[0].body.clauses
    assert (loop.counter_var, loop.list_var, loop.step_size) == ("n", "xs", 1)
    assert loop.empty_clause is original[0] and loop.zero_clause is original[1]


def test_zero_empty_arm_never_reaches_the_rewrite_so_the_shared_witness_is_not_optimizer_coverage_today():
    lowered = _lowered(ZERO_PICK)
    optimized = optimize_program(lowered)
    assert optimized[0] is lowered[0]
    assert isinstance(optimized[0].body, ir.IrCase)


def test_guard_bearing_grouped_arms_are_never_rewritten_and_keep_their_guard_today():
    source = "pick(n, xs) = (_, []) -> nil | (0, [x, .._]) ? x > 0 -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
    lowered = _lowered(source)
    optimized = optimize_program(lowered)
    assert optimized[0] is lowered[0]
    assert [c.guard is not None for c in _clauses(optimized)] == [False, True, False]


def test_surviving_original_arm_information_today():
    """Pins exactly what the rewritten declaration still carries; asserts no absence."""
    lowered = _lowered(NIL_PICK)
    optimized = optimize_program(lowered)
    original = _clauses(lowered)
    survivors = _clauses(optimized)
    assert survivors[0] is original[0] and survivors[1] is original[1]
    assert _arm_record(0, survivors[0]) == _arm_record(0, original[0])
    assert _arm_record(1, survivors[1]) == _arm_record(1, original[1])


# --- retention: optim-keys-retained / d8-arms-retained (RED) ------------------------------------


def test_optim_keys_retained_all_original_arms_stay_reachable_after_optimization():
    lowered = _lowered(NIL_PICK)
    optimized = optimize_program(lowered)
    assert isinstance(optimized[0].body, ir.IrListTraversalLoop)  # the hazardous rewrite really ran
    original = _clauses(lowered)
    retained = _clauses(optimized)
    assert len(original) == 3
    assert len(retained) == len(original), (
        f"optimizer dropped {len(original) - len(retained)} original arm(s): "
        "the recursive arm is absent from IrListTraversalLoop"
    )
    assert retained == original


def test_d8_arm_keys_ordinals_guards_and_provenance_equal_the_unoptimized_ones():
    lowered = _lowered(NIL_PICK)
    optimized = optimize_program(lowered)
    assert isinstance(optimized[0].body, ir.IrListTraversalLoop)
    assert _arms(optimized) == _arms(lowered)
    # keys derived from the optimized node alone must not be accepted as retention
    assert [r[0] for r in _arms(optimized)] == [0, 1, 2]


def test_retention_holds_with_a_later_pattern_clause_and_a_later_other_arity_declaration():
    source = NIL_PICK + "pick(xs) = pick(0, xs)\n"
    lowered = _lowered(source)
    optimized = optimize_program(lowered)
    assert isinstance(optimized[0].body, ir.IrListTraversalLoop)
    assert [type(n).__name__ for n in optimized] == [type(n).__name__ for n in lowered]
    assert optimized[1] is lowered[1]  # later declarations are never reordered, merged or rewritten
    assert _arms(optimized) == _arms(lowered)


# --- observable equivalence with the optimizer on and off ----------------------------------------


@pytest.mark.parametrize(
    "tail",
    ["pick(1, [5, 6])", "[pick(1, [5, 6]), pick(5, [1]), pick(0, [])]", "pick(1.5, [1, 2, 3])"],
    ids=["found", "short-lists", "float-counter"],
)
def test_on_off_agree_for_list_arguments_today(tail):
    source = NIL_PICK + tail
    assert _run(source, optimize=False) == _run(source, optimize=True)


@pytest.mark.parametrize(
    "tail",
    ["pick(0, 7)", 'pick("a", [1])'],
    ids=["non-list-xs", "non-numeric-counter"],
)
def test_on_off_agree_for_arguments_outside_the_rewrite_domain(tail):
    """Pre-existing divergence: the loop returns none("nil") where the case raises its miss error."""
    source = NIL_PICK + tail
    assert _run(source, optimize=False) == _run(source, optimize=True)


# --- A4: retention-aware, domain-exact fast path (B0 amendment, issue #1269) -------------------
#
# The retained original ``IrCase`` semantics are the oracle. These expectations are the
# *unoptimized* results, pinned literally so the oracle is not circular (a rewrite that changed both
# sides would still fail). In-domain inputs (numeric counter, list ``xs``) may use the fast path;
# every out-of-domain input must fall back to the retained case evaluation and reproduce the
# unoptimized value, error text, effects and terminal grouped miss exactly.

_MISS = "Error: No matching case for function pick/2 with arguments {args}\n"

A4_EXACT = [
    # (id, call, stdout, stderr, exit)
    ("in-domain-found", "pick(2, [1, 2, 3])", "3\n", "", 0),
    ("in-domain-offset", "pick(3, [1, 2, 3, 4, 5])", "4\n", "", 0),
    ("in-domain-zero-float", "pick(0.0, [4])", "4\n", "", 0),
    ("in-domain-empty", "pick(1, [])", 'none("nil")\n', "", 0),
    ("in-domain-short", "pick(5, [1])", 'none("nil")\n', "", 0),
    ("in-domain-negative", "pick(-1, [1, 2])", 'none("nil")\n', "", 0),
    ("in-domain-fractional", "pick(1.5, [1, 2, 3])", 'none("nil")\n', "", 0),
    ("ood-int-xs", "pick(0, 7)", "", _MISS.format(args="[0, 7]"), 1),
    ("ood-string-xs", 'pick(0, "ab")', "", _MISS.format(args='[0, "ab"]'), 1),
    ("ood-int-xs-positive-counter", "pick(1, 5)", "", _MISS.format(args="[1, 5]"), 1),
    ("ood-map-xs", "pick(2, {a: 1})", "", _MISS.format(args="[2, {a: 1}]"), 1),
    ("ood-string-counter", 'pick("a", [1])', 'none("type-error", {source: "-", left: "string", right: "int"})\n', "", 0),
    ("ood-list-counter", "pick([1], [2])", 'none("type-error", {source: "-", left: "list", right: "int"})\n', "", 0),
    ("ood-bool-counter", "pick(true, [1])", 'none("nil")\n', "", 0),
    ("ood-none-xs", "pick(0, none)", 'none("nil")\n', "", 0),
]


@pytest.mark.parametrize("case", A4_EXACT, ids=[c[0] for c in A4_EXACT])
def test_a4_unoptimized_semantics_are_the_oracle_and_the_optimizer_reproduces_them_exactly(case):
    _, call, stdout, stderr, status = case
    source = NIL_PICK + call
    expected = (stdout, stderr, status)
    assert _run(source, optimize=False) == expected  # the oracle itself is pinned literally
    assert _run(source, optimize=True) == expected  # fast path or fallback: identical observation


def test_a4_out_of_domain_fallback_preserves_effect_order_and_terminal_grouped_miss():
    source = (
        NIL_PICK
        + 'trace(label, value) = { print(label); value }\n'
        + 'pick(trace("counter", 0), trace("xs", 7))'
    )
    off, on = _run(source, optimize=False), _run(source, optimize=True)
    assert off == ("counter\nxs\n", _MISS.format(args="[0, 7]"), 1)
    assert on == off


def test_a4_in_domain_calls_in_the_same_program_as_out_of_domain_calls_do_not_interfere():
    source = NIL_PICK + '[pick(1, [5, 6]), pick(2, [1, 2, 3]), pick(0, []), pick(9, [1])]'
    assert _run(source, optimize=False) == _run(source, optimize=True) == (
        '[6, 3, none("nil"), none("nil")]\n',
        "",
        0,
    )
    mixed = NIL_PICK + 'pick(1, [5, 6])\npick(0, 7)'
    assert _run(mixed, optimize=False) == _run(mixed, optimize=True)


def test_a4_rewrite_participation_is_unchanged_so_a_decline_cannot_pass_silently():
    """Rewrite-participation control: a safe decline of the rewrite is a separate reviewed amendment.

    The retention-aware fast path keeps the rewrite for the in-domain shape. If the fast path cannot
    preserve semantics and GREEN declines the rewrite instead, this test (and
    ``test_nil_empty_arm_reaches_the_nth_style_rewrite_today``) must be amended explicitly in a
    reviewed commit; they never relax implicitly.
    """
    optimized = optimize_program(_lowered(NIL_PICK))
    assert isinstance(optimized[0].body, ir.IrListTraversalLoop)


def test_legacy_duplicate_after_an_optimized_declaration_is_identical_on_and_off_today():
    source = NIL_PICK + "pick(a, b) = 1\n1"
    off, on = _run(source, optimize=False), _run(source, optimize=True)
    assert off == on == ("", "Error: Duplicate function definition: pick/2\n", 1)


def test_later_other_arity_declaration_is_identical_on_and_off_today():
    source = NIL_PICK + "pick(xs) = pick(0, xs)\n[pick(1, [5, 6]), pick([7])]"
    off, on = _run(source, optimize=False), _run(source, optimize=True)
    assert off == on
    assert off[2] == 0 and off[0] == "[6, 7]\n"


@pytest.mark.parametrize("optimize", [False, True], ids=["unoptimized", "optimized"])
def test_later_pattern_clause_behind_an_all_bind_grouped_header_is_unreachable_and_miss_is_terminal(optimize):
    """D8: the earlier all-bind header wins; its grouped body's miss is terminal (no fall-through)."""
    source = NIL_PICK + 'pick(0, 7) = "special"\npick(0, 7)'
    assert _run(source, optimize=optimize) == (
        "",
        "Error: No matching case for function pick/2 with arguments [0, 7]\n",
        1,
    )


def test_duplicate_arms_inside_one_declaration_are_not_checked_today():
    """Arm keys are retained evidence, not duplicate-check inputs (D8): declaration key only."""
    assert _run("g(x) = (0) -> 1 | (0) -> 2\ng(0)", optimize=True) == ("1\n", "", 0)
    assert _run("g(x) = (0) -> 1 | (0) -> 2\ng(0)", optimize=False) == ("1\n", "", 0)


def test_key_construction_runs_no_user_code_for_arms_today():
    calls: list[str] = []
    lowered = _lowered(NIL_PICK)
    env, _ = fresh_env()
    env.set_host("pick", lambda *a: calls.append("ran"), visibility="entry-only")
    _arms(lowered)
    assert calls == []

