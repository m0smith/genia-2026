"""Slice C RED host-local tests: the pure structural dispatch-key boundary (HL-2).

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-2; Model B design
5.4 and 13.4). The approved design says one pure structural walker *replaces*
``genia.callable._open_dispatch_key`` (which wraps ``_structural_key``); those
existing functions are therefore the test entry points, and no public language
API or new function name is introduced or assumed. If GREEN changes the
internal signature, the assertions below are semantic (what must be equal,
distinct, or rejected) and migrate with it; that migration is recorded as a
test-boundary requirement in the RED evidence note, not as a reason to omit
coverage.

Keys are obtained from the real lowering of ``open f(...) = ...`` clauses (the
only construct whose clause keys exist today) or from directly built Core IR
for malformed/unsupported structures. Exception *classes and wording* for
rejection are not specified by the design, so rejection tests only require that
some Exception is raised and that no host rendering is invoked.

``*_today`` tests pin behavior that is already correct and pass; the others
state approved behavior and fail with a real invariant violation.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from genia import ir
from genia.callable import OpenClauseRecord, _open_dispatch_key, _structural_key
from genia.environment import Env
from genia.interpreter import Parser, lex, lower_program
from genia.pattern_match import IrPatBind, IrPatLiteral, IrPatTuple


def _clause(text: str):
    source = f"open {text}"
    node = lower_program(Parser(lex(source), source=source, filename="<command>").parse_program())[0]
    return node.clauses[0]


def key(text: str) -> tuple:
    clause = _clause(text)
    return _open_dispatch_key(clause.pattern, clause.guard)


def same(a: str, b: str) -> bool:
    return key(a) == key(b)


class _Unrenderable:
    """Unsupported host object that records any attempt to render or compare it."""

    renders = 0

    def __repr__(self) -> str:  # pragma: no cover - the assertion is that it is never called
        type(self).renders += 1
        return "<unrenderable 0xDEADBEEF>"

    __str__ = __repr__


@pytest.fixture(autouse=True)
def _reset_renders():
    _Unrenderable.renders = 0
    yield


# --- typed primitives: Boolean, Integer, floating -----------------------------------------------


def test_boolean_true_and_integer_one_have_distinct_keys():
    assert not same("f(true) = 1", "f(1) = 2")
    assert not same("f(false) = 1", "f(0) = 2")


def test_integer_and_floating_literals_have_distinct_keys():
    assert not same("f(1) = 1", "f(1.0) = 2")
    assert not same("f(0) = 1", "f(0.0) = 2")


def test_keys_do_not_depend_on_host_numeric_equality_or_hashing():
    """Distinct tags must stay distinct as dictionary keys, where host == and hash collide."""
    table = {key("f(true) = 1"): "bool", key("f(1) = 1"): "int", key("f(1.0) = 1"): "float"}
    assert len(table) == 3


def test_floating_literals_with_the_same_binary64_value_share_one_key_today():
    assert same("f(1.0) = 1", "f(1.00000000000000001) = 2")
    assert same("f(0.1) = 1", "f(0.10) = 2")


def test_equal_integer_literals_share_one_key_today():
    assert same("f(7) = 1", "f(7) = 2")
    assert not same("f(7) = 1", "f(8) = 2")


def test_numeric_payload_key_does_not_depend_on_mapping_insertion_order():
    """A tagged numeric payload is structure, not text: reordering fields must not change the key."""
    a = ir.IrLiteral({"kind": "integer", "digits": "1"})
    b = ir.IrLiteral({"digits": "1", "kind": "integer"})
    pattern = IrPatTuple([IrPatBind("x")])
    assert _open_dispatch_key(pattern, a) == _open_dispatch_key(pattern, b)


def test_numeric_payload_kinds_stay_distinct_today():
    pattern = IrPatTuple([IrPatBind("x")])
    integer = ir.IrLiteral({"kind": "integer", "digits": "1"})
    decimal = ir.IrLiteral({"kind": "decimal", "digits": "1"})
    assert _open_dispatch_key(pattern, integer) != _open_dispatch_key(pattern, decimal)


# --- binders: alpha-equivalence, repeats, rest, scope-aware shadowing ----------------------------


def test_alpha_equivalent_pattern_binders_share_a_key_today():
    assert same("f([a, b]) = 1", "f([c, d]) = 2")
    assert same("f(x) ? x > 0 = 1", "f(y) ? y > 0 = 2")


def test_repeated_binder_differs_from_distinct_binders_today():
    assert not same("f(x, x) = 1", "f(a, b) = 2")
    assert same("f(x, x) = 1", "f(a, a) = 2")


def test_rest_binders_participate_and_alpha_normalize_today():
    assert same("f(x, ..r) = 1", "f(y, ..s) = 2")
    assert not same("f(x, ..r) = 1", "f(x, y) = 2")


def test_guards_that_differ_have_distinct_keys_and_free_names_stay_syntactic_today():
    assert not same("f(x) ? x > 0 = 1", "f(x) ? x < 0 = 2")
    assert not same("f(x) ? x > limit = 1", "f(x) ? x > cap = 2")


def test_alpha_equivalent_lambda_parameters_in_a_guard_share_a_key():
    assert same("f(x) ? ((a) -> a)(x) > 0 = 1", "f(y) ? ((b) -> b)(y) > 0 = 2")


def test_inner_binder_that_shadows_a_pattern_binder_is_alpha_normalized():
    """The inner lambda parameter shadows the outer binder; renaming either must not matter."""
    assert same("f(a) ? ((a) -> a)(1) > 0 = 1", "f(b) ? ((b) -> b)(1) > 0 = 2")
    assert same("f(a) ? ((a) -> a)(1) > 0 = 1", "f(b) ? ((a) -> a)(1) > 0 = 2")


def test_reference_to_the_inner_binder_is_not_collapsed_with_a_reference_to_the_outer_slot():
    assert not same("f(a) ? ((p) -> p)(a) > 0 = 1", "f(a) ? ((p) -> a)(a) > 0 = 2")


# --- quoted syntax is data; only active unquotes are references -----------------------------------


def test_quoted_names_are_data_and_never_renamed_today():
    assert not same("f(x) ? x == quote(p) = 1", "f(x) ? x == quote(q) = 2")
    assert same("f(x) ? 1 == quote(x) = 1", "f(y) ? 1 == quote(x) = 2")


def test_active_unquote_at_depth_one_is_an_expression_reference():
    assert same("f(x) ? quasiquote(unquote(x)) == 1 = 1", "f(y) ? quasiquote(unquote(y)) == 1 = 2")


def test_unquote_at_depth_two_is_data_not_a_reference_today():
    assert not same(
        "f(x) ? quasiquote(quasiquote(unquote(x))) == 1 = 1",
        "f(y) ? quasiquote(quasiquote(unquote(y))) == 1 = 2",
    )


def test_doubly_nested_unquote_at_depth_two_is_an_active_reference():
    assert same(
        "f(x) ? quasiquote(quasiquote(unquote(unquote(x)))) == 1 = 1",
        "f(y) ? quasiquote(quasiquote(unquote(unquote(y)))) == 1 = 2",
    )


# --- unsupported and malformed structures are rejected without host rendering ---------------------


def test_unsupported_object_in_a_key_is_rejected_without_calling_its_repr():
    with pytest.raises(Exception):
        _structural_key(_Unrenderable(), {})
    assert _Unrenderable.renders == 0


@pytest.mark.parametrize(
    "bad",
    [_Unrenderable(), {1, 2}, b"bytes", object()],
    ids=["custom-object", "set", "bytes", "plain-object"],
)
def test_unsupported_literal_payload_in_a_pattern_is_rejected_and_never_rendered(bad):
    pattern = IrPatTuple([IrPatLiteral(bad)])
    with pytest.raises(Exception):
        _open_dispatch_key(pattern, None)
    assert _Unrenderable.renders == 0


def test_unsupported_object_in_a_guard_is_rejected_and_never_rendered():
    pattern = IrPatTuple([IrPatBind("x")])
    guard = ir.IrBinary(ir.IrVar("x"), "GT", ir.IrLiteral(_Unrenderable()))
    with pytest.raises(Exception):
        _open_dispatch_key(pattern, guard)
    assert _Unrenderable.renders == 0


@pytest.mark.parametrize(
    "pattern",
    [
        ir.IrLiteral(1),
        SimpleNamespace(items=None),
        IrPatTuple(items=None),
        IrPatTuple(items=[5]),
        IrPatTuple(items=["x"]),
        "not a pattern",
        None,
    ],
    ids=["non-pattern-node", "no-items-namespace", "items-none", "raw-int-item", "raw-str-item", "string", "none"],
)
def test_malformed_pattern_structure_is_rejected_deterministically(pattern):
    """A malformed pattern must not silently become fixed arity zero or a repr-based key."""
    with pytest.raises(Exception):
        _open_dispatch_key(pattern, None)


def test_key_construction_is_deterministic_and_side_effect_free_today():
    first = key("f(x) ? x > 0 = 1")
    assert key("f(x) ? x > 0 = 1") == first


def test_building_a_clause_record_evaluates_neither_guard_nor_pattern_today():
    calls: list[str] = []
    env = Env()
    env.set_host("trace", lambda *a: calls.append("guard ran") or True, visibility="entry-only")
    clause = _clause("f(x) ? trace() = 1")
    OpenClauseRecord(clause.pattern, clause.guard, clause.result, env, clause.span)
    assert calls == []


def test_unrelated_value_types_are_not_a_fallback_for_unknown_ir_classes():
    class Fake(ir.IrNode):  # not a lowered IR class: no key may be derived from its repr
        pass

    pattern = IrPatTuple([IrPatBind("x")])
    guard: Any = Fake()
    with pytest.raises(Exception):
        _open_dispatch_key(pattern, guard)
