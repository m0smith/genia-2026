"""Failing tests for extracting pairs(xs, ys) to prelude — issue #183.

Contract:
- GENIA_STATE.md, Host-backed persistent associative maps section
- GENIA_RULES.md, Host-backed persistent map invariants section

Design:
- docs/design/issue-183-pairs-prelude-extraction.md

## Failing test before implementation

- TestPairsInternalRemoved::test_pairs_internal_not_registered

This fails before implementation because `_pairs` is still registered in the
Python environment and callable from Genia. After implementation removes the
private zipping primitive, referencing `_pairs` should raise an undefined-name
style error.

## Regression tests

The remaining tests pass before and after implementation. They pin the public
`pairs(xs, ys)` behavior while the success path moves from Python to prelude.
"""

import pytest

from genia import make_global_env, run_source


def run(src: str):
    env = make_global_env([])
    return run_source(src, env)


class TestPairsInternalRemoved:
    """The private host zipping primitive must not remain public."""

    def test_pairs_internal_not_registered(self):
        # Before implementation: _pairs is registered and returns [[1, 3], [2, 4]],
        # so pytest.raises fails.
        # After implementation: _pairs is not registered, so an undefined-name
        # style error mentioning _pairs is raised.
        with pytest.raises(Exception, match="(?i)_pairs|undefined|not defined|NameError"):
            run("_pairs([1, 2], [3, 4])")


class TestPairsPublicRegression:
    """Public pairs(xs, ys) keeps the approved observable contract."""

    def test_pairs_equal_lists(self):
        assert run("pairs([1, 2], [3, 4])") == [[1, 3], [2, 4]]

    def test_pairs_shorter_first(self):
        assert run("pairs([1, 2], [10, 20, 30])") == [[1, 10], [2, 20]]

    def test_pairs_shorter_second(self):
        assert run("pairs([1, 2, 3], [10, 20])") == [[1, 10], [2, 20]]

    def test_pairs_empty_first_second_and_both(self):
        assert run("pairs([], [1, 2])") == []
        assert run("pairs([1, 2], [])") == []
        assert run("pairs([], [])") == []

    def test_pairs_items_are_lists_not_tuples(self):
        result = run('pairs(["a", "b"], ["x", "y"])')
        assert result == [["a", "x"], ["b", "y"]]
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, list), f"expected list, got {type(item)}"
            assert not isinstance(item, tuple), "pairs must not return host tuples"
            assert len(item) == 2

    def test_pairs_items_match_list_patterns(self):
        assert run(
            """
            add_pair(p) = ([a, b]) -> a + b
            pairs([1, 2], [3, 4]) |> map(add_pair)
            """
        ) == [4, 6]

    def test_pairs_pipeline_compatibility(self):
        assert run(
            """
            pair_product(p) = ([a, b]) -> a * b
            pairs([1, 2, 3], [10, 20, 30])
              |> map(pair_product)
              |> sum
            """
        ) == 140


class TestPairsErrorRegression:
    """Non-list argument errors keep the exact public TypeError messages."""

    def test_pairs_non_list_first_argument_error(self):
        with pytest.raises(TypeError, match="pairs expected a list as first argument, received int"):
            run("pairs(1, [2])")

    def test_pairs_non_list_second_argument_error(self):
        with pytest.raises(TypeError, match="pairs expected a list as second argument, received string"):
            run('pairs([1], "not-a-list")')

    def test_pairs_empty_first_still_validates_second_argument(self):
        with pytest.raises(TypeError, match="pairs expected a list as second argument, received int"):
            run("pairs([], 1)")

    def test_pairs_flow_argument_error_uses_runtime_type(self):
        with pytest.raises(TypeError, match="pairs expected a list as first argument, received flow"):
            run("pairs(tick(1), [])")
