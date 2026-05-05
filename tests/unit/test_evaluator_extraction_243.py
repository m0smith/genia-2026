"""Structural tests for #243: evaluator core extraction.

Contract reference:  .genia/process/tmp/handoffs/issue-243-evaluator-extraction-preflight/01-contract.md
Design reference:    .genia/process/tmp/handoffs/issue-243-evaluator-extraction-preflight/02-design.md

Import contract tests FAIL before implementation (genia.evaluator does not exist yet).
Backward-compat tests PASS before and after implementation.
Behavior preservation tests PASS before and after implementation (regression guard).
"""

import inspect
import pytest


# ---------------------------------------------------------------------------
# 1. Import contract — each fails with ModuleNotFoundError before implementation
# ---------------------------------------------------------------------------


def test_evaluator_class_importable_from_genia_evaluator():
    from genia.evaluator import Evaluator  # noqa: F401


def test_genia_promise_importable_from_genia_evaluator():
    from genia.evaluator import GeniaPromise  # noqa: F401


def test_genia_meta_env_importable_from_genia_evaluator():
    from genia.evaluator import GeniaMetaEnv  # noqa: F401


def test_quasiquote_node_importable_from_genia_evaluator():
    from genia.evaluator import quasiquote_node  # noqa: F401


def test_quote_node_importable_from_genia_evaluator():
    from genia.evaluator import quote_node  # noqa: F401


# ---------------------------------------------------------------------------
# 2. Import graph contract — each fails before implementation
# ---------------------------------------------------------------------------


def test_evaluator_module_does_not_import_interpreter():
    """evaluator.py must not import from interpreter.py (contract §5 rule 1)."""
    import genia.evaluator
    source = inspect.getsource(genia.evaluator)
    assert "interpreter" not in source, (
        "evaluator.py must not import from interpreter.py"
    )


def test_callable_lazy_import_targets_evaluator_not_interpreter():
    """callable.py lazy import must target genia.evaluator, not genia.interpreter."""
    import genia.callable
    source = inspect.getsource(genia.callable)
    # The lazy import lines must reference evaluator
    assert "from genia.evaluator import Evaluator" in source or \
           "from .evaluator import Evaluator" in source, (
        "callable.py lazy import must target genia.evaluator, not genia.interpreter"
    )
    # The old target must be gone
    assert "from genia.interpreter import Evaluator" not in source, (
        "callable.py must not lazy-import Evaluator from genia.interpreter"
    )
    assert "from .interpreter import Evaluator" not in source, (
        "callable.py must not lazy-import Evaluator from .interpreter"
    )


def test_no_circular_imports():
    """Importing evaluator, interpreter, and callable together must not cycle."""
    import genia.evaluator  # noqa: F401
    import genia.interpreter  # noqa: F401
    import genia.callable  # noqa: F401


# ---------------------------------------------------------------------------
# 3. Backward compatibility — PASS before and after implementation
#    interpreter.py re-imports from evaluator.py so these remain accessible.
# ---------------------------------------------------------------------------


def test_evaluator_still_accessible_via_interpreter():
    """Evaluator remains accessible from interpreter namespace via re-import."""
    from genia.interpreter import Evaluator  # noqa: F401


def test_genia_promise_still_accessible_via_interpreter():
    """GeniaPromise remains accessible from interpreter namespace via re-import."""
    from genia.interpreter import GeniaPromise  # noqa: F401


def test_genia_meta_env_still_accessible_via_interpreter():
    """GeniaMetaEnv remains accessible from interpreter namespace via re-import."""
    from genia.interpreter import GeniaMetaEnv  # noqa: F401


# ---------------------------------------------------------------------------
# 4. Behavior preservation — PASS before and after (regression guard)
#    These do not fail before implementation; they guard against regressions.
# ---------------------------------------------------------------------------

from genia import make_global_env, run_source  # noqa: E402


def _run(src, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    return run_source(src, env)


def test_basic_eval_unchanged():
    """Arithmetic and function calls still work after extraction."""
    assert _run("1 + 2") == 3


def test_function_call_unchanged():
    result = _run("f(x) = x + 1\nf(10)")
    assert result == 11


def test_pipeline_eval_unchanged():
    result = _run("[1,2,3] |> count")
    assert result == 3


def test_pipeline_none_propagation_unchanged():
    """none(reason) propagates through pipeline stages unchanged."""
    from genia.values import is_none
    result = _run("none(\"missing\") |> ((x) -> x + 1)")
    assert is_none(result)


def test_pipeline_some_lifting_unchanged():
    """some(x) is lifted through ordinary pipeline stages."""
    result = _run("some(4) |> ((x) -> x + 1)")
    from genia.values import GeniaOptionSome
    assert isinstance(result, GeniaOptionSome)
    assert result.value == 5


def test_tco_unchanged():
    """Tail-call optimization still works (stack does not overflow)."""
    src = """
count_down(n) =
  0 -> 0 |
  n -> count_down(n - 1)
count_down(10000)
"""
    assert _run(src) == 0


def test_case_pattern_matching_unchanged():
    src = """
describe(n) =
  1 -> "one" |
  2 -> "two" |
  _ -> "other"
describe(2)
"""
    assert _run(src) == "two"


def test_promise_force_unchanged():
    """delay/force still works (GeniaPromise.force calls Evaluator.eval)."""
    result = _run("x = delay(1 + 2)\nforce(x)")
    assert result == 3


def test_quasiquote_unchanged():
    """quasiquote_node still calls Evaluator.eval for unquote resolution."""
    result = _run("x = 42\nquasiquote(unquote(x))")
    assert result == 42


def test_metacircular_env_unchanged():
    """GeniaMetaEnv.extend still calls Evaluator.match_pattern correctly."""
    src = """
env = define(empty_env(), quote(x), 10)
lookup(env, quote(x))
"""
    assert _run(src) == 10


def test_module_autoload_unchanged():
    """Module autoload still resolves through evaluator correctly."""
    result = _run("map((x) -> x * 2, [1,2,3])")
    assert result == [2, 4, 6]


def test_none_propagation_in_call_unchanged():
    """none argument to ordinary function short-circuits the call."""
    from genia.values import is_none
    result = _run("f(x) = x + 1\nf(none(\"missing\"))")
    assert is_none(result)
