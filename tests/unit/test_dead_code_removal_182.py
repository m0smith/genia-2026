"""Failing tests for dead-code removal of _map and _filter — issue #182, Item A.

Contract:  docs/architecture/issue-182-contract.md
Design:    docs/architecture/issue-182-design.md

## Failing tests (before implementation)

- TestDeadCodeRemoved::test_map_internal_not_registered
- TestDeadCodeRemoved::test_filter_internal_not_registered

These fail on current main because _map and _filter ARE registered in
the Python environment. After the env.set calls are removed, referencing
_map or _filter by name will raise a NameError, and these tests will pass.

## Regression tests (pass before and after)

All remaining tests confirm that the public map and filter functions
continue to work identically via the prelude (map_acc / filter_acc /
apply_raw). They guard against accidental breakage during the deletion.
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
# Tests that FAIL before implementation (dead-code removal not yet done)
# ---------------------------------------------------------------------------

class TestDeadCodeRemoved:
    """Contract invariant: _map and _filter must not be registered after Item A.

    These tests assert the post-removal state. They fail on current main
    because the names are still registered and callable.
    """

    def test_map_internal_not_registered(self):
        # _map must not be a resolvable name after removal.
        # Before implementation: _map IS registered → run() returns a list, no error.
        # After implementation: _map is not registered → NameError raised.
        with pytest.raises(Exception, match="(?i)_map|undefined|not defined|NameError"):
            run("_map((x) -> x + 1, [1, 2, 3])")

    def test_filter_internal_not_registered(self):
        # _filter must not be a resolvable name after removal.
        # Before implementation: _filter IS registered → run() returns a list, no error.
        # After implementation: _filter is not registered → NameError raised.
        with pytest.raises(Exception, match="(?i)_filter|undefined|not defined|NameError"):
            run("_filter((x) -> x > 1, [1, 2, 3])")


# ---------------------------------------------------------------------------
# Regression: public map still works (invariants A1, A4, A8, A9)
# ---------------------------------------------------------------------------

class TestMapRegression:
    """Public map must behave identically before and after Item A.

    These pass on current main and must continue to pass after deletion.
    """

    def test_map_basic(self):
        # A1: output elements are f applied to each input element, in order
        assert run("map((x) -> x + 1, [1, 2, 3])") == [2, 3, 4]

    def test_map_empty(self):
        # A4: empty list returns empty list
        assert run("map((x) -> x * 2, [])") == []

    def test_map_preserves_order(self):
        # A1: left-to-right order preserved
        assert run('map((x) -> x + "!", ["a", "b", "c"])') == ["a!", "b!", "c!"]

    def test_map_none_elements_delivered(self):
        # A8: none(...) list elements reach the callback via apply_raw
        assert run("map((o) -> unwrap_or(0, o), [none(\"a\"), some(2), none(\"b\")])") == [0, 2, 0]

    def test_map_named_function(self):
        # A9: named functions work as callbacks
        assert run("double(x) = x * 2\nmap(double, [1, 2, 3])") == [2, 4, 6]


# ---------------------------------------------------------------------------
# Regression: public filter still works (invariants A2, A5, A8, A9)
# ---------------------------------------------------------------------------

class TestFilterRegression:
    """Public filter must behave identically before and after Item A.

    These pass on current main and must continue to pass after deletion.
    """

    def test_filter_basic(self):
        # A2: keeps elements where predicate returns true, in order
        assert run("filter((x) -> x > 1, [1, 2, 3])") == [2, 3]

    def test_filter_empty(self):
        # A5: empty list returns empty list
        assert run("filter((x) -> x > 0, [])") == []

    def test_filter_all_kept(self):
        assert run("filter((x) -> x > 0, [1, 2, 3])") == [1, 2, 3]

    def test_filter_none_kept(self):
        assert run("filter((x) -> x > 10, [1, 2, 3])") == []

    def test_filter_none_elements_delivered(self):
        # A8: none(...) elements reach the predicate callback via apply_raw
        assert run("filter((o) -> some?(o), [some(1), none(\"x\"), some(3)])") == [
            run("some(1)"),
            run("some(3)"),
        ]

    def test_filter_named_function(self):
        # A9: named functions work as predicates
        assert run("positive?(x) = x > 0\nfilter(positive?, [-1, 2, -3, 4])") == [2, 4]


# ---------------------------------------------------------------------------
# Regression: reduce unchanged (invariants A3, A6, A7, A8)
# ---------------------------------------------------------------------------

class TestReduceRegression:
    """reduce must be completely unaffected by Item A.

    _reduce was removed in issue #196; these guard that reduce behavior
    is unchanged regardless of which internal catch-all delegates the error.
    """

    def test_reduce_sum(self):
        # A3: left-to-right accumulation
        assert run("reduce((acc, x) -> acc + x, 0, [1, 2, 3])") == 6

    def test_reduce_empty(self):
        # A6: empty list returns initial accumulator
        assert run("reduce((acc, x) -> acc + x, 42, [])") == 42

    def test_reduce_non_list_error(self):
        # A7: exact TypeError message preserved via _reduce_error catch-all
        with pytest.raises(TypeError, match="reduce expected a list as third argument"):
            run('reduce((acc, x) -> acc + x, 0, "not-a-list")')

    def test_reduce_none_elements_delivered(self):
        # A8: none(...) elements reach the callback
        assert run("reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none(\"x\"), some(3)])") == 4
