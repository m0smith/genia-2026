"""Tests for prelude reduce/map/filter extraction using apply_raw — issue #190.

Extracts reduce, map, and filter from Python host-backed _reduce/_map/_filter
into pure Genia prelude implementations using apply_raw.

Spec:   docs/architecture/issue-190-list-hofs-spec.md
Design: docs/architecture/issue-190-list-hofs-design.md

## Failing vs passing before implementation

Tests marked '# FAILS BEFORE IMPL' will fail with the current Python-backed
implementation because they test F4 (strict boolean predicate contract): the
current filter_fn uses Python truthy() — bool(1) is True, so filter((x)->1, xs)
currently returns the full list. After implementation, the prelude uses
apply_raw(predicate, [x]) == true (strict Genia boolean), so non-boolean
truthy return values (1, "hello", a list) cause the element to be excluded.

All other tests cover spec invariants that already pass (regression guard).
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def run_fmt(src: str) -> str:
    env = make_global_env([])
    return format_debug(run_source(src, env))


# ---------------------------------------------------------------------------
# reduce — invariants R1, R2, R3
# ---------------------------------------------------------------------------

class TestReduceBasic:
    """Spec invariants: R1, R2, R3."""

    def test_sum_non_empty(self):
        # R2, R3: basic left fold
        assert run("reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])") == 10

    def test_product(self):
        # R3: left-to-right order matters for non-commutative ops
        assert run("reduce((acc, x) -> acc * x, 1, [2, 3, 4])") == 24

    def test_string_concat(self):
        # R3: left-to-right order visible in concatenation
        assert run('reduce((acc, x) -> acc + x, "", ["a", "b", "c"])') == "abc"

    def test_empty_list_returns_accumulator(self):
        # R1: base case
        assert run("reduce((acc, x) -> acc + x, 0, [])") == 0

    def test_empty_list_with_non_zero_acc(self):
        # R1: any acc value is returned unchanged
        assert run("reduce((acc, x) -> acc + x, 42, [])") == 42

    def test_single_element(self):
        # R2: reduce([x]) == apply_raw(f, [acc, x])
        assert run("reduce((acc, x) -> acc + x, 10, [5])") == 15

    def test_left_fold_order(self):
        # R3: subtraction is not commutative; fold from left
        # (((10 - 1) - 2) - 3) = 4
        assert run("reduce((acc, x) -> acc - x, 10, [1, 2, 3])") == 4

    def test_with_named_function(self):
        # HOF3: named function works as callback
        assert run("add(a, b) = a + b\nreduce(add, 0, [1, 2, 3])") == 6


class TestReduceNoneElements:
    """Spec invariant: HOF1 — none(...) elements delivered to callback without short-circuit."""

    def test_none_elements_delivered_to_callback(self):
        # HOF1: apply_raw semantics — none("x") does not short-circuit
        src = 'reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])'
        assert run(src) == 4

    def test_all_none_elements(self):
        # HOF1: every element is none(...)
        src = 'reduce((acc, o) -> acc + unwrap_or(0, o), 0, [none("a"), none("b")])'
        assert run(src) == 0

    def test_callback_exception_propagates(self):
        # HOF2: callback exceptions propagate through reduce
        with pytest.raises(Exception):
            run("reduce((acc, x) -> undefined_name, 0, [1])")


class TestReduceTypeError:
    """Spec invariant: R4 — non-Seq-compatible third argument raises Seq-compatible TypeError."""

    def test_string_raises(self):
        with pytest.raises(TypeError, match="reduce expected a Seq-compatible value"):
            run('reduce((a, b) -> a, 0, "not-a-list")')

    def test_int_raises(self):
        with pytest.raises(TypeError, match="received int"):
            run("reduce((a, b) -> a, 0, 42)")

    def test_error_message_exact(self):
        with pytest.raises(TypeError, match="reduce expected a Seq-compatible value \\(list or Flow\\); received string\\."):
            run('reduce((a, b) -> a, 0, "oops")')


class TestReduceFlowCompatible:
    """Spec invariants: #305 — reduce accepts Flow as Seq-compatible source."""

    def test_flow_bounded_evolve_sum(self):
        assert run("inc(n) -> n + 1\nevolve(0, inc) |> take(5) |> reduce((sum, x) -> sum + x, 0)") == 10

    def test_flow_bounded_evolve_product(self):
        assert run("inc(n) -> n + 1\nevolve(1, (n) -> n + 1) |> take(4) |> reduce((acc, x) -> acc * x, 1)") == 24

    def test_flow_option_accumulator(self):
        from genia.values import GeniaOptionSome
        result = run("inc(n) -> n + 1\nevolve(0, inc) |> take(5) |> reduce((acc, x) -> some(x), none)")
        assert isinstance(result, GeniaOptionSome)
        assert result.value == 4


# ---------------------------------------------------------------------------
# map — invariants M1, M2, M3, M4
# ---------------------------------------------------------------------------

class TestMapBasic:
    """Spec invariants: M1, M2, M3, M4."""

    def test_increment_each(self):
        # M2, M3, M4
        assert run("map((x) -> x + 1, [1, 2, 3])") == [2, 3, 4]

    def test_empty_list(self):
        # M1
        assert run("map((x) -> x + 1, [])") == []

    def test_same_length(self):
        # M2: output has same length as input
        result = run("map((x) -> x * 2, [10, 20, 30])")
        assert len(result) == 3

    def test_left_to_right_order(self):
        # M4: element i in result corresponds to element i in input
        assert run('map((x) -> x + "!", ["a", "b", "c"])') == ["a!", "b!", "c!"]

    def test_single_element(self):
        # M3
        assert run("map((x) -> x * 10, [7])") == [70]

    def test_with_named_function(self):
        # HOF3
        assert run("double(x) = x * 2\nmap(double, [1, 2, 3])") == [2, 4, 6]

    def test_pipeline_syntax(self):
        assert run("[1, 2, 3] |> map((x) -> x + 1)") == [2, 3, 4]


class TestMapNoneElements:
    """Spec invariant: HOF1 — none(...) elements delivered to map callback."""

    def test_none_elements_passed_to_callback(self):
        # HOF1
        src = 'map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])'
        assert run(src) == [0, 2, 0]

    def test_all_none_elements(self):
        # HOF1: every element is none(...)
        src = 'map((o) -> unwrap_or(-1, o), [none("x"), none("y")])'
        assert run(src) == [-1, -1]

    def test_callback_exception_propagates(self):
        # HOF2
        with pytest.raises(Exception):
            run("map((x) -> undefined_name, [1])")


# ---------------------------------------------------------------------------
# filter — invariants F1, F2, F3, F4
# ---------------------------------------------------------------------------

class TestFilterBasic:
    """Spec invariants: F1, F2, F3."""

    def test_even_elements(self):
        # F2, F3
        assert run("filter((x) -> x % 2 == 0, [1, 2, 3, 4, 5])") == [2, 4]

    def test_empty_list(self):
        # F1
        assert run("filter((x) -> x > 0, [])") == []

    def test_no_match(self):
        # F1-like: nothing passes predicate
        assert run("filter((x) -> x > 100, [1, 2, 3])") == []

    def test_all_match(self):
        # F3: all elements included when predicate is always true
        assert run("filter((x) -> x > 0, [1, 2, 3])") == [1, 2, 3]

    def test_preserves_relative_order(self):
        # F2: included elements appear in original left-to-right order
        assert run("filter((x) -> x % 2 == 1, [5, 2, 3, 4, 1])") == [5, 3, 1]

    def test_with_named_function(self):
        # HOF3
        assert run("positive?(x) = x > 0\nfilter(positive?, [-1, 2, -3, 4])") == [2, 4]

    def test_pipeline_syntax(self):
        assert run("[1, 2, 3, 4, 5] |> filter((x) -> x % 2 == 0)") == [2, 4]


class TestFilterNoneElements:
    """Spec invariant: HOF1 — none(...) elements delivered to filter predicate."""

    def test_some_predicate_on_option_list(self):
        # HOF1: none("x") is delivered to some?, which returns false
        src = 'filter((o) -> some?(o), [some(1), none("x"), some(3)])'
        result = run(src)
        assert len(result) == 2

    def test_none_predicate_keeps_none_elements(self):
        # HOF1: none? returns true for none elements
        src = 'filter((o) -> none?(o), [some(1), none("x"), some(3)])'
        result = run(src)
        assert len(result) == 1

    def test_callback_exception_propagates(self):
        # HOF2
        with pytest.raises(Exception):
            run("filter((x) -> undefined_name, [1])")


class TestFilterStrictBooleanPredicate:
    """Spec invariant: F4 — predicate must return boolean true or false.

    FAILS BEFORE IMPL: current Python filter_fn uses truthy() which accepts
    any non-none, non-false value (truthy(1) is True, truthy("s") is True).
    After implementation the prelude uses apply_raw(pred, [x]) == true (strict
    Genia boolean), so non-boolean truthy return values cause exclusion.
    """

    def test_int_1_equals_true_in_genia(self):
        # Python: 1 == True, so Genia guard (apply_raw(pred,[x]) == true) passes for int 1.
        # Both old Python _filter (truthy(1)==True) and new prelude (1==true is True) include it.
        # Consistent with any?((x)->1, xs) returning true.
        result = run("filter((x) -> 1, [1, 2, 3])")
        assert result == [1, 2, 3]

    def test_string_return_not_truthy(self):
        # FAILS BEFORE IMPL: currently returns [1, 2] (Python truthy("hello") == True)
        # After impl: returns [] (Genia: "hello" == true is false)
        result = run('filter((x) -> "hello", [1, 2])')
        assert result == []

    def test_list_return_not_truthy(self):
        # FAILS BEFORE IMPL: currently returns [1] (Python truthy([1]) == True)
        # After impl: returns [] (Genia: [1] == true is false)
        result = run("filter((x) -> [1], [1])")
        assert result == []

    def test_false_return_excludes(self):
        # Passes before and after: false correctly excludes
        result = run("filter((x) -> false, [1, 2, 3])")
        assert result == []

    def test_true_return_includes(self):
        # Passes before and after: true correctly includes
        result = run("filter((x) -> true, [1, 2, 3])")
        assert result == [1, 2, 3]

    def test_zero_return_excludes(self):
        # FAILS BEFORE IMPL: truthy(0) == False so currently correct, but
        # this verifies the strict boundary: 0 is not true
        result = run("filter((x) -> 0, [1, 2])")
        assert result == []


# ---------------------------------------------------------------------------
# HOF4 — Flow map/filter behavior unchanged
# ---------------------------------------------------------------------------

class TestFlowDispatchUnchanged:
    """Spec invariant: HOF4 — Flow map/filter path is unaffected by prelude change."""

    def test_flow_map_returns_flow(self):
        # The evaluator intercepts map for GeniaFlow before prelude runs; result is a flow
        from genia.interpreter import GeniaFlow
        env = make_global_env([])
        result = run_source("inc(n) -> n + 1\nevolve(0, inc) |> take(3) |> map((x) -> x + 1)", env)
        assert isinstance(result, GeniaFlow)

    def test_flow_filter_returns_flow(self):
        # The evaluator intercepts filter for GeniaFlow before prelude runs; result is a flow
        from genia.interpreter import GeniaFlow
        env = make_global_env([])
        result = run_source("inc(n) -> n + 1\nevolve(0, inc) |> take(5) |> filter((x) -> x > 2)", env)
        assert isinstance(result, GeniaFlow)


# ---------------------------------------------------------------------------
# Regression: existing callers unchanged (HOF3, HOF4)
# ---------------------------------------------------------------------------

class TestRegressionExistingBehavior:
    """These must pass BEFORE and AFTER implementation (regression guard)."""

    def test_count_uses_reduce(self):
        # count is built on reduce in list.genia
        assert run("count([1, 2, 3, 4, 5])") == 5

    def test_any_with_filter(self):
        # any? and find_opt use same strict-boolean pattern as new filter
        assert run("any?((x) -> x > 3, [1, 2, 3, 4])") is True

    def test_reduce_none_propagation_unchanged(self):
        # Regression from issue #188 test suite
        src = 'reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])'
        assert run(src) == 4

    def test_map_none_propagation_unchanged(self):
        src = 'map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])'
        assert run(src) == [0, 2, 0]

    def test_filter_option_elements_unchanged(self):
        src = 'filter((o) -> some?(o), [some(1), none("x"), some(3)])'
        result = run(src)
        assert len(result) == 2

    def test_reduce_count_case(self):
        # From test_cases: reduce_count.genia
        assert run("reduce((acc, _) -> acc + 1, 0, [10, 20, 30])") == 3
