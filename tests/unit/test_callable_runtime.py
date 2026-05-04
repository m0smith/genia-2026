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
