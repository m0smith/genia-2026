"""Tests for the callable runtime module (genia.callable) — issue #236.

Contract reference:  .genia/process/tmp/handoffs/issue-236-callable-runtime-preflight/01-contract.md
Design reference:    .genia/process/tmp/handoffs/issue-236-callable-runtime-preflight/02-design.md

Import contract tests FAIL before implementation (genia.callable does not exist yet).
Backward-compat tests PASS before and after implementation.
Direct behavior tests FAIL before implementation.
"""

import pytest


# ---------------------------------------------------------------------------
# 1. Import contract — each fails with ModuleNotFoundError before implementation
# ---------------------------------------------------------------------------


def test_genia_function_importable_from_genia_callable():
    from genia.callable import GeniaFunction  # noqa: F401


def test_genia_function_group_importable_from_genia_callable():
    from genia.callable import GeniaFunctionGroup  # noqa: F401


def test_tail_call_importable_from_genia_callable():
    from genia.callable import TailCall  # noqa: F401


def test_eval_with_tco_importable_from_genia_callable():
    from genia.callable import eval_with_tco  # noqa: F401


def test_callable_explicitly_handles_none_importable_from_genia_callable():
    from genia.callable import _callable_explicitly_handles_none  # noqa: F401


def test_none_aware_public_functions_importable_from_genia_callable():
    from genia.callable import _NONE_AWARE_PUBLIC_FUNCTIONS  # noqa: F401


# ---------------------------------------------------------------------------
# 2. Backward compatibility — must still be importable from genia.interpreter
#    PASS before implementation and must still PASS after.
# ---------------------------------------------------------------------------


def test_genia_function_still_importable_from_interpreter():
    from genia.interpreter import GeniaFunction  # noqa: F401


def test_genia_function_group_still_importable_from_interpreter():
    from genia.interpreter import GeniaFunctionGroup  # noqa: F401


def test_tail_call_still_importable_from_interpreter():
    from genia.interpreter import TailCall  # noqa: F401


def test_eval_with_tco_still_importable_from_interpreter():
    from genia.interpreter import eval_with_tco  # noqa: F401


# ---------------------------------------------------------------------------
# Helpers — use lazy imports so the file collects even before genia.callable exists
# ---------------------------------------------------------------------------


def _make_fn(name, params, rest_param=None, docstring=None):
    from genia.callable import GeniaFunction
    from genia.environment import Env
    from genia.ir import IrLiteral
    return GeniaFunction(
        name=name,
        params=list(params),
        rest_param=rest_param,
        docstring=docstring,
        body=IrLiteral(value=None),
        closure=Env(None),
    )


# ---------------------------------------------------------------------------
# 3. _NONE_AWARE_PUBLIC_FUNCTIONS contents
# ---------------------------------------------------------------------------


def test_none_aware_set_contains_apply():
    from genia.callable import _NONE_AWARE_PUBLIC_FUNCTIONS
    assert "apply" in _NONE_AWARE_PUBLIC_FUNCTIONS


def test_none_aware_set_contains_or_else_and_unwrap_or():
    from genia.callable import _NONE_AWARE_PUBLIC_FUNCTIONS
    assert "or_else" in _NONE_AWARE_PUBLIC_FUNCTIONS
    assert "unwrap_or" in _NONE_AWARE_PUBLIC_FUNCTIONS


def test_none_aware_set_contains_option_predicates():
    from genia.callable import _NONE_AWARE_PUBLIC_FUNCTIONS
    assert "some?" in _NONE_AWARE_PUBLIC_FUNCTIONS
    assert "none?" in _NONE_AWARE_PUBLIC_FUNCTIONS


# ---------------------------------------------------------------------------
# 4. TailCall dataclass
# ---------------------------------------------------------------------------


def test_tail_call_holds_fn_and_args():
    from genia.callable import TailCall
    sentinel = object()
    tc = TailCall(fn=sentinel, args=(1, 2, 3))
    assert tc.fn is sentinel
    assert tc.args == (1, 2, 3)


# ---------------------------------------------------------------------------
# 5. GeniaFunctionGroup direct dispatch
# ---------------------------------------------------------------------------


def test_function_group_duplicate_arm_raises_type_error():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x"]))
    with pytest.raises(TypeError, match="Duplicate function definition: f/1"):
        fg.add_clause(_make_fn("f", ["y"]))


def test_function_group_sorted_arities_returns_ordered_list():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x", "y"]))
    fg.add_clause(_make_fn("f", ["x"]))
    assert fg.sorted_arities() == [1, 2]


# ---------------------------------------------------------------------------
# 6. Docstring merging — direct, without the parser
# ---------------------------------------------------------------------------


def test_docstring_group_adopts_first_arm_docstring():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x"], docstring="the doc"))
    assert fg.docstring == "the doc"


def test_docstring_group_keeps_docstring_when_second_arm_has_none():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x"], docstring="the doc"))
    fg.add_clause(_make_fn("f", ["x", "y"], docstring=None))
    assert fg.docstring == "the doc"


def test_docstring_identical_arms_accepted():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x"], docstring="same"))
    fg.add_clause(_make_fn("f", ["x", "y"], docstring="same"))
    assert fg.docstring == "same"


def test_docstring_conflict_raises_type_error():
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn("f", ["x"], docstring="first"))
    with pytest.raises(TypeError, match="Conflicting docstrings for function f"):
        fg.add_clause(_make_fn("f", ["x", "y"], docstring="second"))


# ---------------------------------------------------------------------------
# 7. None-awareness detection
# ---------------------------------------------------------------------------


def test_callable_handles_none_when_attribute_set():
    from genia.callable import _callable_explicitly_handles_none
    fn = lambda x: x  # noqa: E731
    fn.__genia_handles_none__ = True
    assert _callable_explicitly_handles_none(fn, 1) is True


def test_callable_not_handles_none_without_attribute():
    from genia.callable import _callable_explicitly_handles_none
    fn = lambda x: x  # noqa: E731
    assert _callable_explicitly_handles_none(fn, 1) is False


def test_callable_handles_none_via_known_name_in_group():
    from genia.callable import GeniaFunctionGroup, _callable_explicitly_handles_none
    fg = GeniaFunctionGroup(name="apply")
    assert _callable_explicitly_handles_none(fg, 2) is True


def test_callable_not_handles_none_for_unknown_name_group():
    from genia.callable import GeniaFunctionGroup, _callable_explicitly_handles_none
    fg = GeniaFunctionGroup(name="my_unknown_fn_xyz")
    assert _callable_explicitly_handles_none(fg, 1) is False


# ---------------------------------------------------------------------------
# Helpers for invoke_callable tests
# ---------------------------------------------------------------------------


def _make_fn_returning(name, params, return_val, rest_param=None):
    from genia.callable import GeniaFunction
    from genia.environment import Env
    from genia.ir import IrLiteral
    return GeniaFunction(
        name=name,
        params=list(params),
        rest_param=rest_param,
        docstring=None,
        body=IrLiteral(value=return_val),
        closure=Env(None),
    )


def _make_group_1(name, return_val):
    from genia.callable import GeniaFunctionGroup
    fg = GeniaFunctionGroup(name=name)
    fg.add_clause(_make_fn_returning(name, ["x"], return_val))
    return fg


def _make_ir_var(name):
    from genia.ir import IrVar
    return IrVar(name=name)


# ---------------------------------------------------------------------------
# 8. invoke_callable — import contract (FAIL before implementation)
# ---------------------------------------------------------------------------


def test_invoke_callable_importable_from_genia_callable():
    from genia.callable import invoke_callable  # noqa: F401


# ---------------------------------------------------------------------------
# 9. truthy — moved to values.py (FAIL before implementation)
# ---------------------------------------------------------------------------


def test_truthy_importable_from_genia_values():
    from genia.values import truthy  # noqa: F401


def test_truthy_still_importable_from_interpreter():
    from genia.interpreter import truthy  # noqa: F401


def test_truthy_false_for_none():
    from genia.values import truthy, make_none
    assert truthy(make_none("x")) is False


def test_truthy_true_for_nonzero_int():
    from genia.values import truthy
    assert truthy(1) is True


def test_truthy_false_for_zero():
    from genia.values import truthy
    assert truthy(0) is False


# ---------------------------------------------------------------------------
# 10. invoke_callable — plain callable dispatch
# ---------------------------------------------------------------------------


def test_invoke_callable_calls_plain_callable():
    from genia.callable import invoke_callable
    result = invoke_callable(lambda x: x + 1, [41], tail_position=False)
    assert result == 42


def test_invoke_callable_non_callable_raises_type_error():
    from genia.callable import invoke_callable
    with pytest.raises(TypeError, match="pipeline stage expected a callable value"):
        invoke_callable(42, [], tail_position=False)


def test_invoke_callable_plain_callable_tail_position_returns_tail_call():
    from genia.callable import invoke_callable, TailCall
    fn = lambda: 1  # noqa: E731
    result = invoke_callable(fn, [], tail_position=True)
    assert isinstance(result, TailCall)
    assert result.fn is fn


# ---------------------------------------------------------------------------
# 11. invoke_callable — None short-circuit
# ---------------------------------------------------------------------------


def test_invoke_callable_none_short_circuits_before_dispatch():
    from genia.callable import invoke_callable
    from genia.values import make_none
    n = make_none("x")
    result = invoke_callable(lambda v: v, [n], tail_position=False)
    assert result is n


def test_invoke_callable_none_short_circuit_returns_first_none():
    from genia.callable import invoke_callable
    from genia.values import make_none
    n1 = make_none("first")
    n2 = make_none("second")
    result = invoke_callable(lambda a, b: None, [n1, n2], tail_position=False)
    assert result is n1


def test_invoke_callable_none_propagation_skipped_when_flag_set():
    from genia.callable import invoke_callable
    from genia.values import make_none
    n = make_none("x")
    result = invoke_callable(lambda v: 99, [n], tail_position=False, skip_none_propagation=True)
    assert result == 99


# ---------------------------------------------------------------------------
# 12. invoke_callable — GeniaMap dispatch
# ---------------------------------------------------------------------------


def test_invoke_callable_map_arity_1_present_key():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap().put("name", "alice")
    result = invoke_callable(m, ["name"], tail_position=False)
    assert result == "alice"


def test_invoke_callable_map_arity_1_missing_key_returns_none():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap, is_none
    m = GeniaMap()
    result = invoke_callable(m, ["missing"], tail_position=False)
    assert is_none(result)


def test_invoke_callable_map_arity_2_missing_key_returns_default():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap()
    result = invoke_callable(m, ["missing", "fallback"], tail_position=False)
    assert result == "fallback"


def test_invoke_callable_map_arity_2_present_key_ignores_default():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap().put("x", 99)
    result = invoke_callable(m, ["x", "ignored"], tail_position=False)
    assert result == 99


def test_invoke_callable_map_wrong_arity_raises():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap()
    with pytest.raises(TypeError, match="map callable expected 1 or 2 args, got 0"):
        invoke_callable(m, [], tail_position=False)


def test_invoke_callable_map_arity_3_raises():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap()
    with pytest.raises(TypeError, match="map callable expected 1 or 2 args, got 3"):
        invoke_callable(m, ["a", "b", "c"], tail_position=False)


# ---------------------------------------------------------------------------
# 13. invoke_callable — str projector dispatch
# ---------------------------------------------------------------------------


def test_invoke_callable_str_projector_arity_1_present():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap().put("k", "val")
    result = invoke_callable("k", [m], tail_position=False)
    assert result == "val"


def test_invoke_callable_str_projector_arity_2_missing_returns_default():
    from genia.callable import invoke_callable
    from genia.values import GeniaMap
    m = GeniaMap()
    result = invoke_callable("k", [m, "default"], tail_position=False)
    assert result == "default"


def test_invoke_callable_str_projector_non_map_raises():
    from genia.callable import invoke_callable
    with pytest.raises(TypeError, match="string projector expected a map-like target"):
        invoke_callable("k", ["not_a_map"], tail_position=False)


def test_invoke_callable_str_projector_wrong_arity_zero_raises():
    from genia.callable import invoke_callable
    with pytest.raises(TypeError, match="string projector expected 1 or 2 args, got 0"):
        invoke_callable("k", [], tail_position=False)


def test_invoke_callable_str_projector_wrong_arity_three_raises():
    from genia.callable import invoke_callable
    with pytest.raises(TypeError, match="string projector expected 1 or 2 args, got 3"):
        invoke_callable("k", [None, None, None], tail_position=False)


# ---------------------------------------------------------------------------
# 14. invoke_callable — GeniaFunctionGroup dispatch
# ---------------------------------------------------------------------------


def test_invoke_callable_function_group_exact_arity_returns_value():
    from genia.callable import invoke_callable
    fg = _make_group_1("f", 42)
    result = invoke_callable(fg, [0], tail_position=False)
    assert result == 42


def test_invoke_callable_function_group_no_match_raises():
    from genia.callable import invoke_callable
    fg = _make_group_1("f", 0)
    with pytest.raises(TypeError, match="No matching function: f/2"):
        invoke_callable(fg, [1, 2], tail_position=False, callee_node=_make_ir_var("f"))


def test_invoke_callable_function_group_tail_position_returns_tail_call():
    from genia.callable import invoke_callable, TailCall
    fg = _make_group_1("f", 0)
    result = invoke_callable(fg, [1], tail_position=True)
    assert isinstance(result, TailCall)


def test_invoke_callable_function_group_ambiguous_varargs_raises():
    from genia.callable import invoke_callable, GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn_returning("f", [], 0, rest_param="xs"))
    fg.add_clause(_make_fn_returning("f", ["a"], 0, rest_param="xs"))
    with pytest.raises(TypeError, match="Ambiguous function resolution"):
        invoke_callable(fg, [1, 2], tail_position=False)


def test_invoke_callable_function_group_autoload_resolver_called_on_miss():
    from genia.callable import invoke_callable, GeniaFunctionGroup
    fg_original = GeniaFunctionGroup(name="f")
    fg_original.add_clause(_make_fn_returning("f", ["x", "y"], 0))
    fg_resolved = GeniaFunctionGroup(name="f")
    fg_resolved.add_clause(_make_fn_returning("f", ["x"], 7))
    calls = []
    def resolver(name, arity):
        calls.append((name, arity))
        return fg_resolved
    result = invoke_callable(
        fg_original, [1],
        tail_position=False,
        callee_node=_make_ir_var("f"),
        autoload_resolver=resolver,
    )
    assert calls == [("f", 1)]
    assert result == 7


def test_invoke_callable_function_group_autoload_resolver_none_return_raises():
    from genia.callable import invoke_callable, GeniaFunctionGroup
    fg = GeniaFunctionGroup(name="f")
    fg.add_clause(_make_fn_returning("f", ["x", "y"], 0))
    def resolver(name, arity):
        return None
    with pytest.raises(TypeError, match="No matching function: f/1"):
        invoke_callable(
            fg, [1],
            tail_position=False,
            callee_node=_make_ir_var("f"),
            autoload_resolver=resolver,
        )
