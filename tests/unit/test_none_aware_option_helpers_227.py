"""Tests for issue #227 — none-aware callable classification for Option helpers.

Ensures that intended predicate, recovery, and inspection helpers receive
none(...) directly instead of having it short-circuit before reaching them.
Ordinary calls whose bodies do not match none continue to propagate absence.
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str) -> object:
    env = make_global_env([])
    return run_source(src, env)


def _run_flow(src: str) -> object:
    block = "{\ncollect\n" + src + "\n}"
    return run_source(block, make_global_env([]))


# ---------------------------------------------------------------------------
# Predicates — none?(none("x")) and friends
# ---------------------------------------------------------------------------

def test_none_predicate_receives_none_directly():
    assert _run('none?(none("x"))') is True


def test_none_predicate_false_for_some():
    assert _run('none?(some(3))') is False


def test_none_predicate_false_for_plain_value():
    assert _run('none?(42)') is False


def test_is_none_alias_receives_none_directly():
    assert _run('is_none?(none("x"))') is True


def test_is_none_false_for_some():
    assert _run('is_none?(some(3))') is False


def test_some_predicate_false_for_none():
    assert _run('some?(none("x"))') is False


def test_some_predicate_true_for_some():
    assert _run('some?(some(3))') is True


def test_is_some_alias_false_for_none():
    assert _run('is_some?(none("x"))') is False


# ---------------------------------------------------------------------------
# Recovery helpers — or_else / or_else_with receive none(...) directly
# ---------------------------------------------------------------------------

def test_or_else_recovers_from_none():
    assert _run('or_else(none("x"), 42)') == 42


def test_or_else_passes_through_some():
    assert _run('or_else(some(9), 42)') == 9


def test_or_else_with_recovers_from_none():
    assert _run('or_else_with(none("x"), () -> 42)') == 42


def test_or_else_with_passes_through_some():
    assert _run('or_else_with(some(9), () -> 42)') == 9


def test_unwrap_or_recovers_from_none():
    assert _run('unwrap_or(42, none("x"))') == 42


def test_unwrap_or_passes_through_some():
    assert _run('unwrap_or(42, some(9))') == 9


# ---------------------------------------------------------------------------
# Inspection helpers — absence_reason / absence_context / absence_meta
# ---------------------------------------------------------------------------

def test_absence_reason_receives_none_directly():
    assert format_debug(_run('absence_reason(none("x"))')) == 'some("x")'


def test_absence_context_receives_none_directly():
    assert format_debug(_run('absence_context(none("x"))')) == 'none("nil")'


def test_absence_meta_receives_none_directly():
    assert format_debug(_run('absence_meta(none("x"))')) == 'some({reason: "x"})'


# ---------------------------------------------------------------------------
# get / get? results inspectable by is_none? and absence helpers
# ---------------------------------------------------------------------------

def test_get_missing_key_result_is_none():
    assert _run('is_none?(get("b", {a: 1}))') is True


def test_get_q_missing_key_result_is_none():
    assert _run('is_none?(get?("b", {a: 1}))') is True


def test_absence_reason_of_missing_get():
    assert format_debug(_run('absence_reason(get("b", {a: 1}))')) == 'some("missing-key")'


# ---------------------------------------------------------------------------
# Flow-prelude predicates (list?, map?) — none-awareness via (none) -> false arm
# ---------------------------------------------------------------------------

def test_list_predicate_returns_false_for_none():
    assert _run_flow('list?(none("x"))') is False


def test_map_predicate_returns_false_for_none():
    assert _run_flow('map?(none("x"))') is False


def test_list_predicate_true_for_list():
    assert _run_flow('list?([1, 2])') is True


def test_map_predicate_true_for_map():
    assert _run_flow('map?({a: 1})') is True


# ---------------------------------------------------------------------------
# Delegation wrappers (rules_map?, rules_list?) — none-awareness preserved
# ---------------------------------------------------------------------------

def test_rules_map_returns_false_for_none():
    assert _run_flow('rules_map?(none("x"))') is False


def test_rules_list_returns_false_for_none():
    assert _run_flow('rules_list?(none("x"))') is False


def test_rules_map_true_for_nonempty_map():
    assert _run_flow('rules_map?({a: 1})') is True


def test_rules_list_true_for_nonempty_list():
    assert _run_flow('rules_list?([1, 2])') is True


def test_rules_optional_value_returns_default_for_none():
    assert _run_flow('rules_optional_value(none, "key", "default")') == "default"


def test_rules_optional_value_returns_default_map_correctly():
    assert _run_flow('rules_map?(rules_optional_value({}, "ctx", {}))') is True


# ---------------------------------------------------------------------------
# Propagation preserved for ordinary (non-option-aware) calls
# ---------------------------------------------------------------------------

def test_ordinary_call_propagates_none():
    src = 'f(x) = x + 1\nf(none("x"))'
    result = _run(src)
    assert format_debug(result) == 'none("x")'


def test_pipeline_short_circuits_on_none_for_generic_stage():
    result = _run('none("x") |> parse_int')
    assert format_debug(result) == 'none("x")'
