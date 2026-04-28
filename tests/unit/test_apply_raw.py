"""Tests for apply_raw(f, args) — issue #188.

apply_raw invokes a Genia callable with a list of positional arguments,
bypassing the automatic none(...) propagation short-circuit.

Spec: docs/architecture/issue-188-callbacks-spec.md
Design: docs/architecture/issue-188-callbacks-design.md

These tests MUST FAIL before implementation and PASS after.
The exception is the regression group, which must pass both before and after.
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
# 1. Ordinary-value equivalence
#    When no argument is none(...), apply_raw(f, args) == f(args[0], ...)
# ---------------------------------------------------------------------------

class TestApplyRawOrdinaryValue:
    """Spec invariant: ordinary-value-equivalence."""

    def test_named_function(self):
        assert run("inc(x) = x + 1\napply_raw(inc, [41])") == 42

    def test_lambda(self):
        assert run("apply_raw((x) -> x * 2, [21])") == 42

    def test_multi_arg(self):
        assert run("apply_raw((a, b) -> a + b, [10, 32])") == 42

    def test_string_arg(self):
        assert run('apply_raw((s) -> s, ["hello"])') == "hello"

    def test_list_arg(self):
        assert run("apply_raw((xs) -> length(xs), [[1, 2, 3]])") == 3


# ---------------------------------------------------------------------------
# 2. Zero-arg invocation
# ---------------------------------------------------------------------------

class TestApplyRawZeroArg:
    """Spec invariant: ordinary-value-equivalence with empty args list."""

    def test_zero_arg_lambda(self):
        assert run("apply_raw(() -> 42, [])") == 42

    def test_zero_arg_named(self):
        assert run("answer() = 42\napply_raw(answer, [])") == 42


# ---------------------------------------------------------------------------
# 3. Raw invocation — body executes when argument is none(...)
#    This is the core invariant that distinguishes apply_raw from a normal call.
# ---------------------------------------------------------------------------

class TestApplyRawNoneArgBodyExecutes:
    """Spec invariant: raw-invocation."""

    def test_lambda_with_unwrap_or(self):
        # Body executes: unwrap_or(0, none("missing")) = 0
        assert run('apply_raw((o) -> unwrap_or(0, o), [none("missing")])') == 0

    def test_multi_arg_none_in_second_position(self):
        # step(5, none("q")) normally short-circuits to none("q").
        # apply_raw bypasses that: body runs, unwrap_or handles none, 5 + 0 = 5.
        src = 'step = (acc, x) -> acc + unwrap_or(0, x)\napply_raw(step, [5, none("q")])'
        assert run(src) == 5

    def test_named_function_unwraps_none(self):
        src = '\n'.join([
            'safe(x) = unwrap_or(0, x)',
            'apply_raw(safe, [none("err")])',
        ])
        assert run(src) == 0

    def test_some_predicate_on_none_returns_false(self):
        # some? is none-aware but here we confirm apply_raw passes none to any fn
        assert run('apply_raw((x) -> none?(x), [none("x")])') is True

    def test_none_first_arg(self):
        # none in first position — body executes with acc = none("n")
        src = 'apply_raw((acc, x) -> unwrap_or(0, acc) + x, [none("n"), 10])'
        assert run(src) == 10


# ---------------------------------------------------------------------------
# 4. No implicit coercion — none passes through unchanged when not handled
# ---------------------------------------------------------------------------

class TestApplyRawNoImplicitCoercion:
    """Spec invariant: no-implicit-coercion and return-value-as-is."""

    def test_identity_lambda_returns_none_unchanged(self):
        result = run_fmt('apply_raw((x) -> x, [none("y")])')
        assert result == 'none("y")'

    def test_identity_lambda_preserves_none_reason(self):
        result = run_fmt('apply_raw((x) -> x, [none("custom-reason")])')
        assert result == 'none("custom-reason")'

    def test_identity_lambda_preserves_some(self):
        # apply_raw does not unwrap some(...)
        assert run("is_some?(apply_raw((x) -> x, [some(7)]))") is True

    def test_returns_plain_value_unchanged(self):
        # return value is not re-wrapped
        assert run("apply_raw((x) -> x + 1, [10])") == 11


# ---------------------------------------------------------------------------
# 5. Exception propagation — errors inside f propagate through apply_raw
# ---------------------------------------------------------------------------

class TestApplyRawExceptionPropagates:
    """Spec invariant: exception-propagation."""

    def test_arity_mismatch_raises(self):
        # Providing 2 args to a 1-arg function raises a dispatch error
        with pytest.raises(Exception, match="[Nn]o.*match|[Uu]nmatched|[Dd]ispatch|[Aa]rity"):
            run("inc(x) = x + 1\napply_raw(inc, [1, 2])")

    def test_undefined_name_inside_body_propagates(self):
        # NameError from inside the body propagates through apply_raw
        with pytest.raises(NameError, match="undefined_in_body"):
            run("apply_raw((x) -> undefined_in_body, [1])")


# ---------------------------------------------------------------------------
# 6. Error: args is not a list
# ---------------------------------------------------------------------------

class TestApplyRawArgsNotList:
    """Spec §2.5: args must be a list."""

    def test_string_as_args_raises_type_error(self):
        with pytest.raises(TypeError, match="apply_raw expected a list"):
            run('apply_raw((x) -> x, "bad")')

    def test_int_as_args_raises_type_error(self):
        with pytest.raises(TypeError, match="apply_raw expected a list"):
            run("apply_raw((x) -> x, 42)")

    def test_map_as_args_raises_type_error(self):
        with pytest.raises(TypeError, match="apply_raw expected a list"):
            run("apply_raw((x) -> x, {})")

    def test_bool_as_args_raises_type_error(self):
        # bool is not a list (note: none(...) as args short-circuits at the apply_raw call
        # site itself before apply_raw_fn runs, so bool/int/string are the testable cases)
        with pytest.raises(TypeError, match="apply_raw expected a list"):
            run("apply_raw((x) -> x, true)")

    def test_error_message_includes_received_type(self):
        with pytest.raises(TypeError, match="received string"):
            run('apply_raw((x) -> x, "bad")')

    def test_error_message_includes_received_int(self):
        with pytest.raises(TypeError, match="received int"):
            run("apply_raw((x) -> x, 99)")


# ---------------------------------------------------------------------------
# 7. Error: proc is not callable
# ---------------------------------------------------------------------------

class TestApplyRawProcNotCallable:
    """Spec §2.5: non-callable f raises."""

    def test_int_proc_raises(self):
        with pytest.raises(TypeError, match="callable"):
            run("apply_raw(42, [1])")

    def test_string_proc_raises(self):
        with pytest.raises(TypeError):
            run('apply_raw("not-a-fn", [1])')


# ---------------------------------------------------------------------------
# 8. Regression: normal call semantics are unchanged
#    These tests document CURRENT behavior and must pass BEFORE and AFTER
#    the implementation of apply_raw.
# ---------------------------------------------------------------------------

class TestNormalCallUnchangedRegression:
    """Spec invariant: normal-call-unchanged.

    These are NOT apply_raw tests — they prove that introducing apply_raw
    does not alter the existing none-propagation behavior for ordinary calls.
    """

    def test_normal_call_short_circuits_on_none_arg(self):
        # Lambda not detected as none-aware → short-circuits
        result = run_fmt("((x) -> x + 1)(none(\"q\"))")
        assert result == 'none("q")'

    def test_normal_named_call_short_circuits_on_none_arg(self):
        src = 'step = (acc, x) -> acc + unwrap_or(0, x)\nstep(5, none("q"))'
        result = run_fmt(src)
        assert result == 'none("q")'

    def test_reduce_with_none_elements_still_works(self):
        # reduce uses _invoke_raw_from_builtin internally and must continue to work
        src = 'reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])'
        assert run(src) == 4

    def test_map_with_none_elements_still_works(self):
        src = 'map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])'
        assert run(src) == [0, 2, 0]

    def test_filter_with_none_elements_still_works(self):
        src = 'filter((o) -> some?(o), [some(1), none("x"), some(3)])'
        result = run(src)
        assert len(result) == 2
        assert run('is_some?(unwrap_or(none, first(filter((o) -> some?(o), [some(1), none("x"), some(3)]))))') is True

    def test_none_aware_function_still_receives_none(self):
        # unwrap_or is none-aware; it receives none directly in normal calls
        result = run_fmt('unwrap_or(0, none("x"))')
        assert result == "0"
