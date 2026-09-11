"""E18-4 (#794) focused evidence that every equality-like surface uses one relation.

The shared `spec/eval/r18-surface-*.yaml` cases carry the portable evidence.
These tests cover the internal call sites, the Sheet column-name boundary, and
the guarantees that must survive routing — notably that comparing matcher values
never invokes them and that `assert_eq` is not a protected-payload oracle.

Issue contract: .genia/process/tmp/handoffs/e18-4-reconcile-equality-surfaces/01-contract.md
"""

from __future__ import annotations

import math

import pytest

from genia.builtins import make_global_env
from genia.equality import genia_equal
from genia.interpreter import run_source
from genia.sheet import make_sheet
from genia.values import GeniaProtected, symbol


def run(source: str):
    return run_source(source, make_global_env([]))


# --------------------------------------------------------------------------
# cross-surface agreement
# --------------------------------------------------------------------------

# Restricted to expression forms the meta-circular evaluator supports. It has no
# list or Outcome literal ("metacircular eval does not support expression"), so
# those operands are exercised through the other surfaces below instead.
SCALAR_OPERAND_PAIRS = [
    ("1", "1.0", True),
    ("true", "1", False),
    ("false", "0", False),
    ("1", "2", False),
    ('"a"', '"a"', True),
    ("true", "true", True),
    ("1", '"1"', False),
]

COMPOSITE_OPERAND_PAIRS = [
    ("[1, 2]", "[1, 2.0]", True),
    ("[1, 2]", "[2, 1]", False),
    ("some(1)", "some(1.0)", True),
    ("some(1)", "err(1)", False),
    ("quote(a)", '"a"', False),
    ('{"a": 1, "b": 2}', '{"b": 2, "a": 1}', True),
]


@pytest.mark.parametrize("left,right,expected", COMPOSITE_OPERAND_PAIRS)
def test_operator_and_duplicate_binding_agree_on_composites(
    left: str, right: str, expected: bool
) -> None:
    result = run(
        f"""
        dup(a, b) =
          (x, x) -> true |
          (a, b) -> false
        [{left} == {right}, dup({left}, {right}), {left} != {right}]
        """
    )
    operator_result, duplicate_result, negation = result
    assert operator_result is expected
    assert duplicate_result is expected, "duplicate binding disagrees with =="
    assert negation is (not expected)


@pytest.mark.parametrize("left,right,expected", SCALAR_OPERAND_PAIRS)
def test_operator_duplicate_binding_and_meta_all_agree(
    left: str, right: str, expected: bool
) -> None:
    """The decisive invariant: every surface answers as `==` does."""
    result = run(
        f"""
        dup(a, b) =
          (x, x) -> true |
          (a, b) -> false
        e = empty_env()
        [{left} == {right}, dup({left}, {right}), eval(quote({left} == {right}), e), {left} != {right}]
        """
    )
    operator_result, duplicate_result, meta_result, negation = result
    assert operator_result is expected
    assert duplicate_result is expected, "duplicate binding disagrees with =="
    assert meta_result is expected, "meta-evaluator disagrees with =="
    assert negation is (not expected), "!= is not the negation of =="


def test_literal_patterns_agree_with_the_relation() -> None:
    result = run(
        """
        lit_one(v) =
          (1) -> true |
          (v) -> false
        lit_true(v) =
          (true) -> true |
          (v) -> false
        [lit_one(1), lit_one(1.0), lit_one(true), lit_one(2), lit_true(true), lit_true(1)]
        """
    )
    assert result == [True, True, False, False, True, False]


def test_assert_eq_succeeds_exactly_when_the_relation_is_true() -> None:
    passing = run(
        """
        [
          none?(assert_eq(1, 1.0)),
          none?(assert_eq(utf8_encode("hi"), utf8_encode("hi"))),
          none?(assert_eq({"a": 1, "b": 2}, {"b": 2, "a": 1})),
          none?(assert_eq([1, [2]], [1, [2.0]]))
        ]
        """
    )
    assert passing == [True, True, True, True]

    for source in (
        "assert_eq(true, 1)",
        "assert_eq(false, 0)",
        'assert_eq(quote(a), "a")',
        "assert_eq(some(1), err(1))",
    ):
        with pytest.raises(Exception) as excinfo:
            run(source)
        assert "assert_eq failed" in str(excinfo.value), source


def test_meta_evaluator_inequality_agrees_with_the_relation() -> None:
    result = run(
        """
        e = empty_env()
        [eval(quote(true != 1), e), true != 1, eval(quote(1 != 1.0), e), 1 != 1.0]
        """
    )
    assert result == [True, True, False, False]


# --------------------------------------------------------------------------
# Sheet column-name identity
# --------------------------------------------------------------------------


def test_sheet_column_names_that_are_unequal_are_distinct_columns() -> None:
    result = run('columns(sheet([[true, [1]], [1, [2]], ["x", [3]]]))')
    assert result == [True, 1, "x"]


def test_sheet_column_names_that_are_equal_are_still_duplicates() -> None:
    for source in (
        'sheet([[1, [1]], [1.0, [2]]])',
        'sheet([["a", [1]], ["a", [2]]])',
        'sheet([[quote(a), [1]], [quote(a), [2]]])',
    ):
        with pytest.raises(TypeError, match="unique column names"):
            run(source)


def test_nan_column_name_is_rejected_as_non_reflexive() -> None:
    """A column whose name does not equal itself cannot denote a stable column."""
    with pytest.raises(TypeError):
        make_sheet([[math.nan, [1]]])
    with pytest.raises(TypeError):
        make_sheet([[[1, math.nan], [1]]])


def test_protected_column_name_rejection_is_unchanged_and_non_disclosing() -> None:
    sentinel = "PAYLOAD_SENTINEL_794"
    protected = GeniaProtected(sentinel, object(), symbol("purpose"))
    with pytest.raises(TypeError, match="protected values cannot be Sheet column names") as excinfo:
        make_sheet([[protected, [1]]])
    assert sentinel not in str(excinfo.value)


# --------------------------------------------------------------------------
# guarantees that must survive routing
# --------------------------------------------------------------------------


def test_comparing_matcher_values_never_invokes_them() -> None:
    """A named pattern compared as a *value* is identity-bearing, not applied."""
    result = run(
        """
        pattern Even(v) = if_match(v, (x) -> x % 2 == 0)
        e = Even
        [e == e, e == Even]
        """
    )
    assert result == [True, True]


def test_assert_eq_is_not_a_protected_payload_oracle() -> None:
    provider = object()
    same_a = GeniaProtected("SECRET", provider, symbol("u"))
    same_b = GeniaProtected("SECRET", provider, symbol("u"))
    different = GeniaProtected("OTHER", provider, symbol("u"))

    # Whatever assert_eq does, it must do the same for both pairs.
    assert genia_equal(same_a, same_b) == genia_equal(same_a, different)
    assert genia_equal(same_a, same_b) is False


def test_literal_pattern_mismatch_is_a_mismatch_not_an_error() -> None:
    result = run(
        """
        lit(v) =
          (1) -> "one" |
          (v) -> "other"
        [lit(true), lit("1"), lit([1]), lit(some(1))]
        """
    )
    assert result == ["other", "other", "other", "other"]


def test_index_handle_comparison_returns_a_boolean_by_identity() -> None:
    """Identity-bearing per the approved contract, so `==` yields a boolean."""
    from genia.retrieval import GeniaIndexHandle

    handle = GeniaIndexHandle(object(), "space", 2, object(), ())
    other = GeniaIndexHandle(object(), "space", 2, object(), ())
    assert genia_equal(handle, handle) is True
    assert genia_equal(handle, other) is False
