"""Slice C RED host-local tests: source/direct-IR twins, optimizer equivalence, group index, races.

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-1 (legacy part),
HL-3, HL-7, HL-8). Lowered Core IR, optimizer node selection, the arity-keyed
group index and the binding lock are Python implementation details; the
portable observations are the shared ``model-b-c-*`` cases that these tests
re-run through a second path.

HL-7 evaluates every source-expressible shared case through a lowered-IR twin
(unoptimized Core IR) and through ``run_source`` (optimized) and requires both
to agree with each other *and* with the YAML oracle, so two equal failures
cannot pass vacuously. HL-8 asserts the same equivalence with the optimizer on
and off for the optimizer-sensitive programs.

Not implemented here (no approved internal API names exist yet, so any
assertion would invent an interface): the ordered record API and owner token
of HL-1, the pure key walker of HL-2 and arm-key retention of HL-8
(`optim-keys-retained`, `d8-arms-retained-not-checked`). They are recorded in
the RED evidence note as blocked on the GREEN design naming those internals.
"""

from __future__ import annotations

import threading
from typing import Any

import pytest

import genia
from genia.environment import _BINDING_LOCK
from genia.evaluator import Evaluator
from genia.interpreter import Parser, lex, lower_program
from genia.optimizer import optimize_program
from genia.utf8 import format_debug
from tests.unit.model_b_slice_c_support import fresh_env, outcome
from tools.spec_runner.loader import discover_specs

_SPECS = {s.name: s for s in discover_specs()[0] if s.name.startswith("model-b-c-")}
SOURCE_CASES = sorted(
    name
    for name, spec in _SPECS.items()
    if spec.category in {"eval", "error"} and not spec.module_entry and not spec.stdin and not spec.fixtures
)


def _lowered(source: str, filename: str = "<command>"):
    return lower_program(Parser(lex(source), source=source, filename=filename).parse_program())


def _run_ir(source: str, *, optimize: bool) -> tuple[str, str, int]:
    """Evaluate lowered Core IR (optionally optimized) and render like the CLI does."""
    env, printed = fresh_env()
    try:
        nodes = _lowered(source)
        if optimize:
            nodes = optimize_program(nodes)
        value = Evaluator(env).eval_program(nodes)
    except Exception as error:  # noqa: BLE001
        return "".join(printed), f"Error: {error}\n", 1
    rendered = "" if value is None or repr(value) == "none('nil')" else format_debug(value) + "\n"
    return "".join(printed) + rendered, "", 0


def _run_source(source: str) -> tuple[str, str, int]:
    result = outcome(source)
    if result.error is not None:
        return "".join(result.printed), f"Error: {result.error}\n", 1
    value = result.value
    rendered = "" if value is None or repr(value) == "none('nil')" else format_debug(value) + "\n"
    return "".join(result.printed) + rendered, "", 0


def test_source_case_selection_is_non_vacuous():
    assert len(SOURCE_CASES) >= 100


@pytest.mark.parametrize("name", SOURCE_CASES)
def test_source_and_direct_ir_twins_agree_with_each_other_and_the_oracle(name):
    spec = _SPECS[name]
    expected = (spec.expected_stdout, spec.expected_stderr, spec.expected_exit_code)
    twin = _run_ir(spec.source, optimize=False)
    optimized_twin = _run_ir(spec.source, optimize=True)
    via_source = _run_source(spec.source)
    assert twin == optimized_twin == via_source, name
    assert twin == expected, name


# --- HL-8: optimizer on/off equivalence for optimizer-sensitive programs ---------------------

OPTIMIZER_PROGRAMS = {
    "pick-recursion": (
        "pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
        "pick(1, [5, 6])"
    ),
    "late-declaration-of-another-shape": (
        "pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
        "pick(xs) = pick(0, xs)\n"
        "[pick(1, [5, 6]), pick([7])]"
    ),
    "late-duplicate-after-optimized-declaration": (
        "pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
        "pick(a, b) = 1\n"
        "pick(1, [5, 6])"
    ),
}


@pytest.mark.parametrize("label", sorted(OPTIMIZER_PROGRAMS))
def test_optimizer_on_and_off_agree_for_collection_recursion_programs(label):
    source = OPTIMIZER_PROGRAMS[label]
    assert _run_ir(source, optimize=False) == _run_ir(source, optimize=True) == _run_source(source), label


def test_optimized_declaration_followed_by_a_pattern_clause_matches_the_unoptimized_result():
    source = (
        "pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)\n"
        'pick(0, 7) = "special"\n'
        "[pick(0, 7), pick(1, [5, 6])]"
    )
    off = _run_ir(source, optimize=False)
    on = _run_ir(source, optimize=True)
    assert off == on
    assert off[2] == 0 and off[0] == '["special", 6]\n'


# --- HL-1 (legacy part): the arity index stays consistent for legacy-only groups ---------------


@pytest.mark.parametrize(
    "source",
    [
        "f(x) = x\ng(y) = y\nf(x, y) = x + y",
        "f(a, ..r) = a\nf(a, b, c) = a",
        "f() = 0\nf(a) = a\nf(a, b) = a",
    ],
    ids=["noncontiguous", "rest-and-fixed", "three-arities"],
)
def test_legacy_group_arity_index_matches_its_function_table_today(source):
    env, _ = fresh_env()
    genia.run_source(source, env)
    group = env.get("f")
    assert group.sorted_arities() == sorted(group.functions)
    for arity in group.sorted_arities():
        assert group.get(arity) is group.functions[arity]
        assert group.get(arity).arity == arity


def test_rejected_legacy_duplicate_leaves_the_group_unchanged_today():
    env, _ = fresh_env()
    genia.run_source("f(x) = x", env)
    before = dict(env.get("f").functions)
    assert outcome("f(y) = y", env=env).error_class == "TypeError"
    assert env.get("f").functions == before


# --- HL-3: writer atomicity, reentrancy and the binding lock -----------------------------------

JOIN_SECONDS = 20.0


def _run_threads(*targets) -> None:
    threads = [threading.Thread(target=t, daemon=True) for t in targets]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(JOIN_SECONDS)
    assert not any(t.is_alive() for t in threads), "thread did not finish within the bounded join"


def test_two_writers_declaring_the_same_pattern_key_publish_exactly_once():
    env, _ = fresh_env()
    barrier = threading.Barrier(2, timeout=JOIN_SECONDS)
    results: list[Any] = []

    def writer(source):
        def run():
            barrier.wait()
            results.append(outcome(source, env=env))

        return run

    _run_threads(writer('f(0) = "first"'), writer('f(0) = "second"'))
    failures = [r for r in results if r.error is not None]
    assert len(results) == 2 and len(failures) == 1
    assert failures[0].error_class == "OpenFunctionDuplicateClauseError"
    assert genia.run_source("f(0)", env) in {"first", "second"}


def test_declaration_racing_an_immutable_rebind_never_bypasses_the_policy():
    env, _ = fresh_env()
    barrier = threading.Barrier(2, timeout=JOIN_SECONDS)
    results: dict[str, Any] = {}

    def declare():
        barrier.wait()
        results["declare"] = outcome('f(0) = "zero"', env=env)

    def bind():
        barrier.wait()
        results["bind"] = outcome("f =: 5", env=env)

    _run_threads(declare, bind)
    assert "model-b-not-implemented" not in (results["declare"].message or "")
    declared_ok = results["declare"].error is None
    bound_ok = results["bind"].error is None
    assert declared_ok != bound_ok, "exactly one writer may win"
    value = env.get("f")
    assert (value == 5) if bound_ok else (value is not None and value != 5)


def test_annotation_that_reenters_evaluation_neither_deadlocks_nor_loses_either_declaration():
    env, _ = fresh_env()

    def reenter_doc():
        genia.run_source('g(0) = "inner"', env)
        return "doc text"

    env.set_host("reenter_doc", reenter_doc, visibility="entry-only")
    box: dict[str, Any] = {}

    def run():
        box["outcome"] = outcome('@doc reenter_doc()\nf(0) = "outer"', env=env)

    _run_threads(run)
    assert box["outcome"].error is None, box["outcome"].message
    assert genia.run_source("[f(0), g(0)]", env) == ["outer", "inner"]


def test_user_code_never_runs_while_the_binding_lock_is_held_for_legacy_annotations_today():
    env, _ = fresh_env()
    observed: list[bool] = []

    def probe_doc():
        acquired = _BINDING_LOCK.acquire(blocking=False)
        if acquired:
            _BINDING_LOCK.release()
        observed.append(acquired)
        return "doc text"

    env.set_host("probe_doc", probe_doc, visibility="entry-only")
    genia.run_source("@doc probe_doc()\nf(x) = x", env)
    assert observed == [True]


def test_user_code_never_runs_while_the_binding_lock_is_held_for_pattern_annotations():
    env, _ = fresh_env()
    observed: list[bool] = []

    def probe_doc():
        acquired = _BINDING_LOCK.acquire(blocking=False)
        if acquired:
            _BINDING_LOCK.release()
        observed.append(acquired)
        return "doc text"

    env.set_host("probe_doc", probe_doc, visibility="entry-only")
    genia.run_source('@doc probe_doc()\nf(0) = "zero"', env)
    assert observed == [True]
