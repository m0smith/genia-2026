"""Failing tests for _reduce_error primitive — issue #196.

Contract:  docs/architecture/issue-196-reduce-fallthrough-contract.md
Design:    docs/architecture/issue-196-reduce-fallthrough-design.md

## Failing tests (before implementation)

- TestReduceErrorPrimitive::test_reduce_error_registered
- TestReduceErrorPrimitive::test_reduce_error_flow_message
- TestReduceErrorPrimitive::test_reduce_error_string_message
- TestReduceErrorPrimitive::test_reduce_error_int_message
- TestReduceInternalRemoved::test_reduce_internal_not_registered

### Why they fail on current main

- tests_reduce_error_*: `_reduce_error` is not yet registered in the env.
  Calling `_reduce_error(...)` in Genia raises NameError, not the expected
  TypeError. `pytest.raises(TypeError, ...)` does not catch NameError, so the
  NameError propagates and the test fails.

- test_reduce_internal_not_registered: `_reduce` IS still registered. Calling
  `_reduce(f, acc, 42)` raises TypeError("reduce expected a list as third
  argument, received int"). The match pattern checks for "_reduce", "undefined",
  "not defined", or "NameError" — none of which appear in that TypeError message
  (note: "reduce" ≠ "_reduce"). The match fails and the test fails.

## Regression tests (pass before and after)

- TestReduceNonListRegression — reduce(f, acc, non_list) continues to raise
  the exact same TypeError via the arm-3 catch-all, whether that arm delegates
  to `_reduce` (current) or `_reduce_error` (after implementation).
"""

import pytest

from genia import make_global_env, run_source


def run(src: str):
    env = make_global_env([])
    return run_source(src, env)


# ---------------------------------------------------------------------------
# Tests that FAIL before implementation
# ---------------------------------------------------------------------------


class TestReduceErrorPrimitive:
    """_reduce_error must be registered and raise TypeError with the exact message.

    All four tests fail on current main because _reduce_error is not yet
    registered. Each call raises NameError which pytest.raises(TypeError)
    does not catch, causing the test to fail with the unexpected NameError.
    """

    def test_reduce_error_registered(self):
        # _reduce_error must be callable from Genia.
        # Before implementation: NameError("Undefined name: _reduce_error") → FAILS.
        # After implementation: TypeError "...received int" → PASSES.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received int"):
            run("_reduce_error(42)")

    def test_reduce_error_flow_message(self):
        # _reduce_error must produce the exact message for a flow value.
        # Before implementation: NameError → FAILS.
        # After implementation: TypeError "...received flow" → PASSES.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received flow"):
            run("_reduce_error(tick(3))")

    def test_reduce_error_string_message(self):
        # _reduce_error must produce the exact message for a string value.
        # Before implementation: NameError → FAILS.
        # After implementation: TypeError "...received string" → PASSES.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received string"):
            run('_reduce_error("hello")')

    def test_reduce_error_int_message(self):
        # Duplicate arity path: verify _reduce_error(xs) for a second int value.
        # Before implementation: NameError → FAILS.
        # After implementation: TypeError "...received int" → PASSES.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received int"):
            run("_reduce_error(99)")


class TestReduceInternalRemoved:
    """_reduce must no longer be registered in the env after the change.

    Fails on current main because _reduce IS registered and raises TypeError
    (not NameError) when called with a non-list third argument. The match
    pattern looks for "_reduce", "undefined", "not defined", or "NameError" —
    none of which appear in the current TypeError message — so the match fails
    and the test fails.
    """

    def test_reduce_internal_not_registered(self):
        # Before implementation: _reduce IS registered; calling it with a non-list
        #   raises TypeError("reduce expected a list as third argument, received int").
        #   The match pattern "(?i)_reduce|undefined|not defined|NameError" does NOT
        #   match that message ("reduce" ≠ "_reduce") → test FAILS.
        # After implementation: _reduce is removed; calling it raises
        #   NameError("Undefined name: _reduce"); match on "_reduce" succeeds → PASSES.
        with pytest.raises(Exception, match="(?i)_reduce|undefined|not defined|NameError"):
            run("_reduce((acc, x) -> acc + x, 0, 42)")


# ---------------------------------------------------------------------------
# Regression: reduce non-list error message is preserved (pass before and after)
# ---------------------------------------------------------------------------


class TestReduceNonListRegression:
    """reduce(f, acc, non_list) must raise the exact TypeError via arm 3.

    These tests pass on current main (arm 3 delegates to _reduce) and must
    continue to pass after implementation (arm 3 delegates to _reduce_error).
    The observable user-visible behavior — the exact error message — is identical
    in both cases. These are regression guards, not failing tests.
    """

    def test_reduce_non_list_flow(self):
        # I1: reduce with a Flow xs raises the exact TypeError message.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received flow"):
            run("reduce((acc, x) -> acc + x, 0, tick(3))")

    def test_reduce_non_list_string(self):
        # I2: reduce with a string xs raises the exact TypeError message.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received string"):
            run('reduce((acc, x) -> acc + x, 0, "not-a-list")')

    def test_reduce_non_list_int(self):
        # reduce with an int xs raises the exact TypeError message.
        with pytest.raises(TypeError, match="reduce expected a list as third argument, received int"):
            run("reduce((acc, x) -> acc + x, 0, 42)")

    def test_reduce_list_unaffected(self):
        # I4: normal list reduce accumulates left-to-right, unchanged.
        assert run("reduce((acc, x) -> acc + x, 0, [1, 2, 3])") == 6

    def test_reduce_empty_list_unaffected(self):
        # I3: empty list reduce returns the initial accumulator, unchanged.
        assert run("reduce((acc, x) -> acc + x, 99, [])") == 99

    def test_reduce_none_elements_delivered(self):
        # I5: none(...) list elements reach the callback via apply_raw, unchanged.
        assert run("reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none(\"x\"), some(3)])") == 4
