"""Failing tests for issue #184 — extract validation and defaulting helpers to prelude.

Contract:  docs/architecture/issue-184-validation-defaulting-contract.md
Design:    docs/architecture/issue-184-validation-defaulting-design.md

Three new internal helpers added to flow.genia:
  map?(v)                       — true iff v is a Genia map value
  list?(v)                      — true iff v is a Genia list value
  get_or(key, target, default)  — unwrap_or(default, get(key, target))

Three delegation updates in flow.genia:
  rules_map?         → delegates to map?
  rules_list?        → delegates to list?
  rules_optional_value → delegates to get_or

BEFORE implementation:
  Groups 1–3 (TestMapPredicate, TestListPredicate, TestGetOr) FAIL because
  map?, list?, get_or do not exist yet.  After flow.genia loads the helpers
  are still absent → NameError.

  Groups 4–5: most tests PASS.  However, test_none_false in each group FAILS
  before implementation: the inline bodies of rules_map? and rules_list? use
  plain wildcard arms (`(_) -> false`) which do NOT count as explicitly
  handling none, so Genia's none-propagation fires and returns none('nil')
  instead of false.  After implementation, delegation to map? and list?
  (which have explicit (none) -> false arms) corrects this.

  Group 6 (TestRulesOptionalValueDelegation): all tests PASS before and after.

  Group 7 (TestRulesPipelineRegression): all tests PASS before and after.

AFTER implementation:
  All groups PASS.

Loading mechanism:
  Internal helpers (map?, list?, get_or, rules_map?, rules_list?,
  rules_optional_value) are not registered with register_autoload.  They
  become reachable only after flow.genia is loaded by some registered name.
  The helper run_flow() references `collect` (registered) inside a block to
  trigger that load, then evaluates the target expression.
"""

import pytest

from genia import make_global_env, run_source


def run_flow(expr: str):
    """Evaluate expr after loading flow.genia.

    Puts `collect` at the top of a block to trigger the autoload of
    flow.genia; the block then evaluates expr and returns its value.
    """
    src = "{\ncollect\n" + expr + "\n}"
    return run_source(src, make_global_env([]))


# ---------------------------------------------------------------------------
# Group 1 — map?(v)
# FAILS before implementation: map? is not defined in flow.genia yet.
# Contract invariants covered: 1, 2 (map? true), 3, 4, 5 (map? false).
# ---------------------------------------------------------------------------

class TestMapPredicate:
    """map?(v) returns true for any map value, false for everything else."""

    # --- true cases ---

    def test_empty_map(self):
        assert run_flow("map?({})") is True

    def test_single_entry_map(self):
        assert run_flow("map?({a: 1})") is True

    def test_multi_entry_map(self):
        assert run_flow("map?({x: 1, y: 2, z: 3})") is True

    def test_string_key_map(self):
        assert run_flow('map?({"key": "value"})') is True

    # --- false cases ---

    def test_empty_list_is_false(self):
        assert run_flow("map?([])") is False

    def test_nonempty_list_is_false(self):
        assert run_flow("map?([1, 2])") is False

    def test_string_is_false(self):
        assert run_flow('map?("hello")') is False

    def test_number_is_false(self):
        assert run_flow("map?(42)") is False

    def test_bool_true_is_false(self):
        assert run_flow("map?(true)") is False

    def test_bool_false_is_false(self):
        assert run_flow("map?(false)") is False

    def test_none_is_false(self):
        assert run_flow("map?(none)") is False

    def test_none_with_reason_is_false(self):
        assert run_flow('map?(none("missing"))') is False

    def test_some_is_false(self):
        assert run_flow("map?(some(1))") is False

    # --- total function: never raises, never returns none ---

    def test_returns_bool_not_none(self):
        result = run_flow("map?({})")
        assert result is True or result is False

    def test_does_not_raise_on_any_value(self):
        # spot-check a few unexpected types
        assert run_flow("map?(42)") is False
        assert run_flow("map?(true)") is False
        assert run_flow('map?("x")') is False


# ---------------------------------------------------------------------------
# Group 2 — list?(v)
# FAILS before implementation: list? is not defined in flow.genia yet.
# Contract invariants covered: 3, 4 (list? true), 5, 6 (list? false).
# ---------------------------------------------------------------------------

class TestListPredicate:
    """list?(v) returns true for any list value, false for everything else."""

    # --- true cases ---

    def test_empty_list(self):
        assert run_flow("list?([])") is True

    def test_single_element_list(self):
        assert run_flow("list?([1])") is True

    def test_multi_element_list(self):
        assert run_flow("list?([1, 2, 3])") is True

    def test_nested_list(self):
        assert run_flow("list?([[1], [2]])") is True

    def test_list_of_maps(self):
        assert run_flow("list?([{a: 1}, {b: 2}])") is True

    # --- false cases ---

    def test_empty_map_is_false(self):
        assert run_flow("list?({})") is False

    def test_nonempty_map_is_false(self):
        assert run_flow("list?({a: 1})") is False

    def test_string_is_false(self):
        assert run_flow('list?("hello")') is False

    def test_number_is_false(self):
        assert run_flow("list?(99)") is False

    def test_bool_is_false(self):
        assert run_flow("list?(true)") is False

    def test_none_is_false(self):
        assert run_flow("list?(none)") is False

    def test_some_is_false(self):
        assert run_flow("list?(some([1, 2]))") is False

    # --- total function ---

    def test_returns_bool_not_none(self):
        result = run_flow("list?([])")
        assert result is True or result is False


# ---------------------------------------------------------------------------
# Group 3 — get_or(key, target, default)
# FAILS before implementation: get_or is not defined in flow.genia yet.
# Contract invariants covered: 6 (get_or semantics table).
# ---------------------------------------------------------------------------

class TestGetOr:
    """get_or(key, target, default) returns value at key or default."""

    # --- key present ---

    def test_key_present_returns_value(self):
        assert run_flow('get_or("k", {k: "v"}, "d")') == "v"

    def test_key_present_returns_non_string(self):
        assert run_flow('get_or("n", {n: 42}, 0)') == 42

    def test_key_present_returns_map(self):
        assert run_flow('get_or("a", get_or("inner", {inner: {a: 1}}, {}), 0)') == 1

    def test_key_present_boolean_value(self):
        assert run_flow('get_or("flag", {flag: true}, false)') is True

    # --- key absent: default is returned ---

    def test_empty_map_returns_default(self):
        assert run_flow('get_or("k", {}, "d")') == "d"

    def test_wrong_key_returns_default(self):
        assert run_flow('get_or("k", {other: 1}, "d")') == "d"

    def test_default_is_number(self):
        assert run_flow('get_or("x", {}, 0)') == 0

    def test_default_is_list(self):
        assert run_flow('get_or("x", {}, [])') == []

    def test_default_is_false(self):
        assert run_flow('get_or("x", {}, false)') is False

    # --- none target: default is returned ---

    def test_none_target_returns_default(self):
        assert run_flow('get_or("k", none, "d")') == "d"

    def test_structured_none_target_returns_default(self):
        assert run_flow('get_or("k", none("missing"), "d")') == "d"

    # --- some(map) target: key is found through option-lifting in get ---

    def test_some_map_target_key_found(self):
        # get's maybe-aware lifting: some({k: "v"}) → get sees {k: "v"}
        assert run_flow('get_or("k", some({k: "v"}), "d")') == "v"

    # --- default type is preserved exactly ---

    def test_default_string_preserved(self):
        result = run_flow('get_or("x", {}, "fallback")')
        assert result == "fallback"

    def test_default_zero_preserved(self):
        result = run_flow('get_or("x", {}, 0)')
        assert result == 0


# ---------------------------------------------------------------------------
# Group 4 — rules_map? delegation (PASSES before and after)
# These validate the delegation chain is correct AFTER implementation and
# provide a regression baseline showing behavior is identical to pre-change.
# Contract invariants covered: 7 (rules_map? == map?).
# ---------------------------------------------------------------------------

class TestRulesMapDelegation:
    """rules_map? produces identical results via delegation to map?."""

    def test_empty_map_true(self):
        assert run_flow("rules_map?({})") is True

    def test_nonempty_map_true(self):
        assert run_flow("rules_map?({a: 1})") is True

    def test_list_false(self):
        assert run_flow("rules_map?([])") is False

    def test_string_false(self):
        assert run_flow('rules_map?("x")') is False

    def test_number_false(self):
        assert run_flow("rules_map?(42)") is False

    def test_none_false(self):
        assert run_flow("rules_map?(none)") is False

    def test_some_false(self):
        assert run_flow("rules_map?(some({}))") is False


# ---------------------------------------------------------------------------
# Group 5 — rules_list? delegation (PASSES before and after)
# Contract invariants covered: 8 (rules_list? == list?).
# ---------------------------------------------------------------------------

class TestRulesListDelegation:
    """rules_list? produces identical results via delegation to list?."""

    def test_empty_list_true(self):
        assert run_flow("rules_list?([])") is True

    def test_nonempty_list_true(self):
        assert run_flow("rules_list?([1, 2])") is True

    def test_map_false(self):
        assert run_flow("rules_list?({})") is False

    def test_string_false(self):
        assert run_flow('rules_list?("x")') is False

    def test_number_false(self):
        assert run_flow("rules_list?(99)") is False

    def test_none_false(self):
        assert run_flow("rules_list?(none)") is False

    def test_some_of_list_false(self):
        # some([1,2]) is not itself a list — it's a some-wrapped value
        assert run_flow("rules_list?(some([1, 2]))") is False


# ---------------------------------------------------------------------------
# Group 6 — rules_optional_value delegation (PASSES before and after)
# Contract invariants covered: 9 (rules_optional_value == get_or).
# ---------------------------------------------------------------------------

class TestRulesOptionalValueDelegation:
    """rules_optional_value produces identical results via delegation to get_or."""

    def test_key_present(self):
        assert run_flow('rules_optional_value({k: "v"}, "k", "d")') == "v"

    def test_key_absent_returns_default(self):
        assert run_flow('rules_optional_value({}, "k", "d")') == "d"

    def test_none_returns_default(self):
        assert run_flow('rules_optional_value(none, "k", "d")') == "d"

    def test_default_number(self):
        assert run_flow('rules_optional_value({}, "x", 0)') == 0

    def test_existing_record_key(self):
        # mirrors actual usage in rules_result_record
        assert run_flow('rules_optional_value({record: "new"}, "record", "old")') == "new"

    def test_existing_ctx_key(self):
        # mirrors actual usage in rules_result_ctx
        assert run_flow('rules_optional_value({ctx: "ctx_val"}, "ctx", {})') == "ctx_val"

    def test_missing_ctx_key_default_map(self):
        # Genia map values are not Python dicts; verify via rules_map? that default {} was returned
        assert run_flow('rules_map?(rules_optional_value({}, "ctx", {}))') is True


# ---------------------------------------------------------------------------
# Group 7 — full rules pipeline regression (PASSES before and after)
# Contract invariant 10: all callers of the delegation wrappers produce
# identical results before and after the change.
# ---------------------------------------------------------------------------

class TestRulesPipelineRegression:
    """Full rules/refine pipeline must work identically before and after."""

    def _run_flow_src(self, src: str) -> list:
        env = make_global_env(stdin_data=src.splitlines())
        return run_source("stdin |> lines |> collect", env)

    def test_rules_identity_stage(self):
        """rules() with no fns is an identity stage."""
        env = make_global_env(stdin_data=["a", "b", "c"])
        result = run_source(
            "stdin |> lines |> rules() |> collect",
            env,
        )
        assert result == ["a", "b", "c"]

    def test_rules_emit(self):
        """A rule emitting values produces output."""
        env = make_global_env(stdin_data=["x", "y"])
        result = run_source(
            "stdin |> lines |> rules((r, _) -> rule_emit(r)) |> collect",
            env,
        )
        assert result == ["x", "y"]

    def test_rules_skip(self):
        """A rule returning none skips the item."""
        env = make_global_env(stdin_data=["a", "b"])
        result = run_source(
            "stdin |> lines |> rules((r, _) -> none) |> collect",
            env,
        )
        assert result == []

    def test_rules_ctx_accumulates(self):
        """ctx persists across items in rules."""
        env = make_global_env(stdin_data=["1", "2", "3"])
        result = run_source(
            """
            stdin |> lines
              |> rules(
                  (r, ctx) -> some({
                    emit: [unwrap_or(0, get("count", ctx)) + 1],
                    ctx: {count: unwrap_or(0, get("count", ctx)) + 1}
                  })
                )
              |> collect
            """,
            env,
        )
        assert result == [1, 2, 3]

    def test_rules_halt(self):
        """halt: true stops processing remaining rules for that item."""
        env = make_global_env(stdin_data=["a"])
        result = run_source(
            """
            stdin |> lines
              |> rules(
                  (r, _) -> some({emit: ["first"], halt: true}),
                  (r, _) -> some({emit: ["second"]})
                )
              |> collect
            """,
            env,
        )
        assert result == ["first"]

    def test_rules_invalid_emit_type_raises(self):
        """emit not a list raises a clear error."""
        env = make_global_env(stdin_data=["a"])
        with pytest.raises(RuntimeError, match="invalid-rules-result"):
            run_source(
                'stdin |> lines |> rules((r, _) -> some({emit: "bad"})) |> run',
                env,
            )

    def test_rules_invalid_halt_type_raises(self):
        """halt not a boolean raises a clear error."""
        env = make_global_env(stdin_data=["a"])
        with pytest.raises(RuntimeError, match="invalid-rules-result"):
            run_source(
                'stdin |> lines |> rules((r, _) -> some({halt: "yes"})) |> run',
                env,
            )

    def test_refine_alias_works(self):
        """refine is an alias for rules and must continue to work."""
        env = make_global_env(stdin_data=["p", "q"])
        result = run_source(
            "stdin |> lines |> refine((r, _) -> step_emit(r)) |> collect",
            env,
        )
        assert result == ["p", "q"]

    def test_flow_not_wrapped_in_some_after_option_lifting(self):
        """Flow values must not be wrapped in Some when emerging from option-lifting stages.

        When an earlier stage produces GeniaOptionSome(flow) via option lifting,
        refine and subsequent stages must receive the bare flow, not Some(flow).
        Regression for issue #228.
        """
        env = make_global_env(stdin_data=["a", "b"])
        result = run_source(
            "some(stdin) |> lines |> refine((r, _) -> step_emit(r)) |> collect",
            env,
        )
        assert result == ["a", "b"]
