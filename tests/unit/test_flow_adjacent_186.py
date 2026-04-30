"""Failing tests for issue #186 — move rule_*/step_* constructors from fn.genia to flow.genia.

Contract:  docs/architecture/issue-186-flow-adjacent-contract.md  (if committed)
Design:    docs/architecture/issue-186-flow-adjacent-design.md

The rule/refine result constructors currently live in fn.genia and are registered
to autoload from std/prelude/fn.genia.  After implementation they must live in
flow.genia and autoload from std/prelude/flow.genia.

BEFORE implementation (current state):
  Group 1 (TestAutoloadPaths):
    All tests FAIL — autoload paths still point to std/prelude/fn.genia.

  Group 2 (TestRuleHelperValues):
    All tests PASS — rule_* helpers produce the correct values.

  Group 3 (TestStepHelperAliases):
    All tests PASS — step_* helpers delegate to rule_*.

  Group 4 (TestRulesAndRefineIntegration):
    All tests PASS — rules/refine still accept helper results.

  Group 5 (TestHigherOrderAndCoload):
    All tests PASS — helpers work as higher-order values.

AFTER implementation (target state):
  All groups PASS.
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env():
    return make_global_env([])


def _run(src: str):
    return run_source(src, _env())


def _run_flow(src: str, stdin_lines=None):
    """Run src with an optional stdin list."""
    return run_source(src, make_global_env(stdin_lines or []))


# ---------------------------------------------------------------------------
# Group 1 — Autoload path assertions
# FAILS before implementation: paths still point to std/prelude/fn.genia.
# PASSES after implementation: paths point to std/prelude/flow.genia.
# ---------------------------------------------------------------------------

class TestAutoloadPaths:
    """Assert that every rule_*/step_* helper autoloads from flow.genia."""

    EXPECTED_PATH = "std/prelude/flow.genia"

    _NAMES_ARITY_0 = [
        "rule_skip",
        "step_skip",
        "rule_halt",
        "step_halt",
    ]

    _NAMES_ARITY_1 = [
        "rule_emit",
        "step_emit",
        "rule_emit_many",
        "step_emit_many",
        "rule_set",
        "step_set",
        "rule_ctx",
        "step_ctx",
    ]

    _NAMES_ARITY_3 = [
        "rule_step",
        "step_step",
    ]

    @pytest.mark.parametrize("name", _NAMES_ARITY_0)
    def test_arity0_autoloads_from_flow_genia(self, name):
        env = _env()
        path = env.root().autoloads.get((name, 0))
        assert path == self.EXPECTED_PATH, (
            f"{name}/0 autoloads from {path!r}, expected {self.EXPECTED_PATH!r}"
        )

    @pytest.mark.parametrize("name", _NAMES_ARITY_1)
    def test_arity1_autoloads_from_flow_genia(self, name):
        env = _env()
        path = env.root().autoloads.get((name, 1))
        assert path == self.EXPECTED_PATH, (
            f"{name}/1 autoloads from {path!r}, expected {self.EXPECTED_PATH!r}"
        )

    @pytest.mark.parametrize("name", _NAMES_ARITY_3)
    def test_arity3_autoloads_from_flow_genia(self, name):
        env = _env()
        path = env.root().autoloads.get((name, 3))
        assert path == self.EXPECTED_PATH, (
            f"{name}/3 autoloads from {path!r}, expected {self.EXPECTED_PATH!r}"
        )


# ---------------------------------------------------------------------------
# Group 2 — rule_* return values
# PASSES before and after implementation (behavioral regression).
# ---------------------------------------------------------------------------

class TestRuleHelperValues:
    """rule_* constructors must produce exact Genia value shapes."""

    def test_rule_skip_returns_none(self):
        result = _run("rule_skip()")
        assert format_debug(result) == 'none("nil")'

    def test_rule_emit_returns_some_with_emit_list(self):
        result = _run("rule_emit(42)")
        assert format_debug(result) == 'some({emit: [42]})'

    def test_rule_emit_many_returns_some_with_emit_list(self):
        result = _run("rule_emit_many([1, 2, 3])")
        assert format_debug(result) == 'some({emit: [1, 2, 3]})'

    def test_rule_emit_many_empty_list(self):
        result = _run("rule_emit_many([])")
        assert format_debug(result) == 'some({emit: []})'

    def test_rule_set_returns_some_with_record(self):
        result = _run('rule_set("new_record")')
        assert format_debug(result) == 'some({record: "new_record"})'

    def test_rule_ctx_returns_some_with_ctx(self):
        result = _run("rule_ctx({count: 1})")
        assert format_debug(result) == 'some({ctx: {count: 1}})'

    def test_rule_halt_returns_some_with_halt_true(self):
        result = _run("rule_halt()")
        assert format_debug(result) == 'some({halt: true})'

    def test_rule_step_returns_combined_map(self):
        result = _run('rule_step("rec", {k: 1}, ["out"])')
        assert format_debug(result) == 'some({record: "rec", ctx: {k: 1}, emit: ["out"]})'


# ---------------------------------------------------------------------------
# Group 3 — step_* are exact aliases for rule_*
# PASSES before and after implementation (behavioral regression).
# ---------------------------------------------------------------------------

class TestStepHelperAliases:
    """step_* must return identical values to their rule_* counterparts."""

    def test_step_skip_equals_rule_skip(self):
        assert format_debug(_run("step_skip()")) == format_debug(_run("rule_skip()"))

    def test_step_emit_equals_rule_emit(self):
        assert format_debug(_run("step_emit(99)")) == format_debug(_run("rule_emit(99)"))

    def test_step_emit_many_equals_rule_emit_many(self):
        src_step = "step_emit_many([10, 20])"
        src_rule = "rule_emit_many([10, 20])"
        assert format_debug(_run(src_step)) == format_debug(_run(src_rule))

    def test_step_set_equals_rule_set(self):
        assert format_debug(_run('step_set("x")')) == format_debug(_run('rule_set("x")'))

    def test_step_ctx_equals_rule_ctx(self):
        assert format_debug(_run("step_ctx({n: 0})")) == format_debug(_run("rule_ctx({n: 0})"))

    def test_step_halt_equals_rule_halt(self):
        assert format_debug(_run("step_halt()")) == format_debug(_run("rule_halt()"))

    def test_step_step_equals_rule_step(self):
        src_step = 'step_step("r", {}, ["v"])'
        src_rule = 'rule_step("r", {}, ["v"])'
        assert format_debug(_run(src_step)) == format_debug(_run(src_rule))


# ---------------------------------------------------------------------------
# Group 4 — rules/refine integration
# PASSES before and after implementation (behavioral regression).
# ---------------------------------------------------------------------------

class TestRulesAndRefineIntegration:
    """rules() and refine() must still accept rule_*/step_* helper results."""

    def test_rules_identity_zero_rules(self):
        result = _run_flow(
            "stdin |> lines |> rules() |> collect",
            stdin_lines=["a", "b", "c"],
        )
        assert result == ["a", "b", "c"]

    def test_rules_with_rule_emit(self):
        result = _run_flow(
            "stdin |> lines |> rules((r, _) -> rule_emit(r + r)) |> collect",
            stdin_lines=["x", "y"],
        )
        assert result == ["xx", "yy"]

    def test_rules_with_rule_skip(self):
        result = _run_flow(
            "stdin |> lines |> rules((r, _) -> rule_skip()) |> collect",
            stdin_lines=["a", "b"],
        )
        assert result == []

    def test_rules_with_rule_emit_many(self):
        result = _run_flow(
            "stdin |> lines |> rules((r, _) -> rule_emit_many([r, r + \"!\"])) |> collect",
            stdin_lines=["hi"],
        )
        assert result == ["hi", "hi!"]

    def test_rules_halt_stops_later_rules(self):
        result = _run_flow(
            """
            stop(r, ctx) = rule_halt()
            emit(r, ctx) = rule_emit(r)
            stdin |> lines |> rules(stop, emit) |> collect
            """,
            stdin_lines=["a", "b"],
        )
        assert result == []

    def test_refine_with_step_emit(self):
        result = _run_flow(
            "stdin |> lines |> refine((r, _) -> step_emit(r + \"!\")) |> collect",
            stdin_lines=["hello"],
        )
        assert result == ["hello!"]

    def test_refine_with_step_skip(self):
        result = _run_flow(
            "stdin |> lines |> refine((r, _) -> step_skip()) |> collect",
            stdin_lines=["a", "b"],
        )
        assert result == []

    def test_rules_ctx_persists_across_items(self):
        result = _run_flow(
            """
            acc(record, ctx) = {
              total = unwrap_or(0, get("total", ctx)) + record
              rule_step(record, {total: total}, [total])
            }
            stdin |> lines |> map(parse_int) |> keep_some |> rules(acc) |> collect
            """,
            stdin_lines=["1", "2", "3"],
        )
        assert result == [1, 3, 6]

    def test_invalid_rules_result_reports_prefix(self):
        with pytest.raises(RuntimeError, match="invalid-rules-result:"):
            _run_flow(
                'stdin |> lines |> rules((r, _) -> "not-an-option") |> collect',
                stdin_lines=["x"],
            )

    def test_invalid_rules_emit_non_list_reports_prefix(self):
        with pytest.raises(RuntimeError, match="invalid-rules-result:"):
            _run_flow(
                'stdin |> lines |> rules((r, _) -> some({emit: "not-a-list"})) |> collect',
                stdin_lines=["x"],
            )


# ---------------------------------------------------------------------------
# Group 5 — higher-order and co-load use
# PASSES before and after implementation (behavioral regression).
# ---------------------------------------------------------------------------

class TestHigherOrderAndCoload:
    """rule_*/step_* must be usable as higher-order values and must co-load
    correctly when referenced before rules/refine in the same program."""

    def test_rule_emit_usable_as_higher_order_value(self):
        result = _run("map_some(rule_emit, some(7))")
        assert format_debug(result) == 'some(some({emit: [7]}))'

    def test_step_emit_usable_as_higher_order_value(self):
        result = _run("map_some(step_emit, some(7))")
        assert format_debug(result) == 'some(some({emit: [7]}))'

    def test_rule_emit_referenced_before_rules_in_same_program(self):
        """rule_emit must autoload independently before rules is referenced."""
        result = _run_flow(
            """
            r = rule_emit(99)
            stdin |> lines |> rules((_, _) -> r) |> collect
            """,
            stdin_lines=["x"],
        )
        assert result == [99]

    def test_step_emit_referenced_before_refine_in_same_program(self):
        """step_emit must autoload independently before refine is referenced."""
        result = _run_flow(
            """
            s = step_emit(42)
            stdin |> lines |> refine((_, _) -> s) |> collect
            """,
            stdin_lines=["x"],
        )
        assert result == [42]

    def test_rule_skip_usable_as_higher_order_value(self):
        """rule_skip() result must be usable as a value that signals no-effect."""
        result = _run("is_none?(rule_skip())")
        assert result is True
