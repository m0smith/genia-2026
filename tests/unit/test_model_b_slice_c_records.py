"""Slice C RED host-local tests: ordered declaration records, identity, index (HL-1).

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-1; design 5.2).
The design says an ordinary group gets "ordered declaration records and a
stable owner/defining-name token" while the arity map "can remain an index
where valid, but cannot be the semantic record store". No field names for
those are approved, so nothing here reads one. Instead the tests pin the
invariants that only a genuine ordered record store can satisfy, through
boundaries that exist today:

* dispatch results (declaration order decides first-match among several
  clauses of one shape; a store keyed only by arity cannot even hold them),
* group identity (``env.get`` objects, alias liveness),
* the arity index (``sorted_arities``/``get``), which must stay a consistent
  *index*, never one entry per record,
* construction-time duplicate rejection with first/duplicate provenance, and
  unchanged state after a rejected declaration.

A reference model (an ordinary Python list of ``(label, matcher)`` in
declaration order) computes the expected result for every ordering of three
distinct-key same-arity clauses, interleaved with an unrelated declaration, so
a store that sorts, dedupes by arity, reverses or overwrites fails.

The one property that cannot be expressed without an approved internal name
(the record/owner-token fields themselves) is recorded as a proposed
test-boundary amendment in the RED evidence note rather than faked here.
"""

from __future__ import annotations

import itertools

import pytest

import genia
from genia.callable import GeniaFunction, GeniaFunctionGroup
from genia import ir
from tests.unit.model_b_slice_c_support import fresh_env, outcome

CLAUSES = {
    "zero": ('f(0) = "zero"', lambda a: a == 0),
    "big": ('f(x) ? x > 5 = "big"', lambda a: a > 5),
    "any": ('f(x) = "any"', lambda a: True),
}
ARGS = [0, 7, 3]


def _expected(order):
    results = []
    for arg in ARGS:
        results.append(next(label for label in order if CLAUSES[label][1](arg)))
    return results


@pytest.mark.parametrize("order", list(itertools.permutations(CLAUSES)), ids=lambda o: "-".join(o))
def test_declaration_order_decides_first_match_across_noncontiguous_declarations(order):
    lines = []
    for index, label in enumerate(order):
        lines.append(CLAUSES[label][0])
        if index == 0:
            lines.append("g(y) = y")  # unrelated declaration between clauses of f
    lines.append("[f(0), f(7), f(3)]")
    result = outcome("\n".join(lines))
    assert result.error is None, result.message
    assert result.value == _expected(order)


def test_group_identity_and_alias_liveness_survive_every_later_declaration():
    env, _ = fresh_env()
    genia.run_source('f(0) = "zero"', env)
    group = env.get("f")
    genia.run_source("a = f", env)
    assert env.get("a") is group
    genia.run_source('f(x) ? x > 5 = "big"', env)
    genia.run_source('f(x) = "any"', env)
    assert isinstance(env.get("f"), GeniaFunctionGroup)
    assert env.get("f") is group and env.get("a") is group
    assert genia.run_source("[a(0), a(7), a(3)]", env) == ["zero", "big", "any"]


def test_arity_index_stays_one_entry_per_shape_not_one_per_record():
    env, _ = fresh_env()
    genia.run_source('f(0) = "zero"\nf(x) ? x > 5 = "big"\nf(x) = "any"\nf(a, b) = a + b', env)
    group = env.get("f")
    arities = group.sorted_arities()
    assert arities == [1, 2]
    assert group.get(1) is not None and group.get(2) is not None
    assert group.get(3) is None


def test_a_later_clause_never_overtakes_an_earlier_catch_all():
    result = outcome('f(x) = "any"\nearly = f(0)\nf(0) = "zero"\n[early, f(0)]')
    assert result.error is None, result.message
    assert result.value == ["any", "any"]  # a later clause never overtakes an earlier catch-all


def test_duplicate_is_rejected_before_publication_with_first_and_duplicate_provenance():
    env, _ = fresh_env()
    genia.run_source('f(0) = "a"\ng(y) = y\nf(x) = "b"', env, filename="<command>")
    group = env.get("f")
    before = (group.sorted_arities(), genia.run_source("[f(0), f(9)]", env))
    failure = outcome('\n\n\nf(0) = "c"', env=env)
    assert failure.error_class == "OpenFunctionDuplicateClauseError"
    assert failure.message == (
        "open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key "
        "shape=('fixed', 1) (first at <command>:1, duplicate at <command>:4)"
    )
    assert env.get("f") is group
    assert (group.sorted_arities(), genia.run_source("[f(0), f(9)]", env)) == before
    assert before[1] == ["a", "b"]


def test_state_is_unchanged_after_a_rejected_declaration_in_a_session_and_the_name_stays_usable():
    env, _ = fresh_env()
    genia.run_source('f(0) = "zero"', env)
    group = env.get("f")
    failure = outcome('f(0) = "again"', env=env)
    assert failure.error_class == "OpenFunctionDuplicateClauseError"
    genia.run_source('f(1) = "one"', env)
    assert env.get("f") is group
    assert genia.run_source("[f(0), f(1)]", env) == ["zero", "one"]


def test_two_clauses_of_one_shape_cannot_be_held_by_the_legacy_arity_table_today():
    """Equivalent all-bind headers remain duplicates at GREEN; preserve rejection."""
    group = GeniaFunctionGroup("f")
    env, _ = fresh_env()
    pattern_free = [
        GeniaFunction("f", ["x"], None, None, ir.IrLiteral(1), env),
        GeniaFunction("f", ["y"], None, None, ir.IrLiteral(2), env),
    ]
    group.add_clause(pattern_free[0])
    with pytest.raises(TypeError, match="Duplicate function definition: f/1"):
        group.add_clause(pattern_free[1])
    assert group.sorted_arities() == [1] and len(group.functions) == 1



# --- discrimination self-check: the oracle above rejects every non-record store ------------------


def _dispatch(store: str, order, arg):
    matchers = [(label, CLAUSES[label][1]) for label in order]
    if store == "ordered-records":
        pass
    elif store == "arity-last-wins":  # legacy table keyed by arity only, later overwrites earlier
        matchers = matchers[-1:]
    elif store == "arity-first-wins":
        matchers = matchers[:1]
    elif store == "sorted-by-label":
        matchers = sorted(matchers)
    elif store == "reversed":
        matchers = matchers[::-1]
    for label, matches in matchers:
        if matches(arg):
            return label
    return None


@pytest.mark.parametrize("store", ["arity-last-wins", "arity-first-wins", "sorted-by-label", "reversed"])
def test_the_ordering_oracle_rejects_stores_that_are_not_ordered_records(store):
    orders = list(itertools.permutations(CLAUSES))
    honest = [[_dispatch("ordered-records", o, a) for a in ARGS] for o in orders]
    assert honest == [_expected(o) for o in orders]
    faulty = [[_dispatch(store, o, a) for a in ARGS] for o in orders]
    assert faulty != honest
