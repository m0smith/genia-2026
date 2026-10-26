"""Slice C GREEN repair R2 (#1269, PR #1270): guard-local lexical normalization.

PYTHON REFERENCE HOST ONLY. Immutable declarations inside guard blocks introduce
lexical binders: the initializer is keyed under the bindings visible before the
declaration, the binder enters scope afterwards, shadowing is honoured, free
references stay syntactically distinct, and block scopes end with the block.
"""

from __future__ import annotations

from genia import ir
from genia.interpreter import Parser, lex, lower_program
from tests.unit.model_b_slice_c_support import dispatch_key


def key(text: str) -> tuple:
    source = f"open {text}"
    node = lower_program(Parser(lex(source), source=source, filename="<command>").parse_program())[0]
    clause = node.clauses[0]
    return dispatch_key(clause.pattern, clause.guard)


def test_renamed_guard_local_is_alpha_equivalent():
    assert key("f(x) ? { a =: x; a > 0 } = 1") == key("f(y) ? { b =: y; b > 0 } = 2")


def test_lambda_guard_block_locals_are_alpha_equivalent():
    assert key("f(x) ? ((p) -> { a =: p; a > x })(1) = 1") == key("f(y) ? ((q) -> { b =: q; b > y })(1) = 1")


def test_sequential_locals_are_alpha_equivalent_and_order_sensitive():
    a = key("f(x) ? { a =: x; b =: a; b > 0 } = 1")
    assert a == key("f(y) ? { c =: y; d =: c; d > 0 } = 1")
    assert a != key("f(x) ? { a =: x; b =: x; b > 0 } = 1")


def test_initializer_resolves_before_binder_enters_scope():
    # `a =: a` reads the OUTER a (free here); it must not self-reference the new binder.
    assert key("f(x) ? { a =: a; a > 0 } = 1") != key("f(x) ? { a =: x; a > 0 } = 1")
    assert key("f(x) ? { a =: a; a > 0 } = 1") == key("f(x) ? { b =: a; b > 0 } = 1")
    assert key("f(x) ? { a =: a; a > 0 } = 1") != key("f(x) ? { b =: b; b > 0 } = 1")


def test_local_shadows_outer_pattern_variable():
    assert key("f(x) ? { x =: 1; x > 0 } = 1") == key("f(y) ? { y =: 1; y > 0 } = 1")
    assert key("f(x) ? { x =: 1; x > 0 } = 1") == key("f(y) ? { z =: 1; z > 0 } = 1")
    assert key("f(x) ? { x =: 1; x > 0 } = 1") != key("f(x) ? { z =: 1; x > 0 } = 1")


def test_free_references_stay_distinct():
    assert key("f(x) ? { a =: 1; a > zed } = 1") != key("f(x) ? { a =: 1; a > other } = 1")
    assert key("f(x) ? { a =: 1; a > zed } = 1") == key("f(y) ? { b =: 1; b > zed } = 1")


def test_outer_scope_restored_after_block():
    # After the inner block, `a` is not bound: the trailing `a` is a free reference.
    one = key("f(x) ? ({ a =: x; a > 0 } && a > 0) = 1")
    two = key("f(x) ? ({ b =: x; b > 0 } && a > 0) = 1")
    assert one == two
    assert one != key("f(x) ? ({ a =: x; a > 0 } && b > 0) = 1")
    assert one != key("f(x) ? ({ a =: x; a > 0 } && x > 0) = 1")


def test_keying_does_not_execute_initializers():
    calls = []
    source = "open f(x) ? { a =: boom(); a > 0 } = 1"
    node = lower_program(Parser(lex(source), source=source, filename="<command>").parse_program())[0]
    clause = node.clauses[0]
    assert dispatch_key(clause.pattern, clause.guard) is not None
    assert calls == []


def test_immutable_bind_node_is_lexical_in_blocks():
    block = ir.IrBlock([ir.IrImmutableBind("a", ir.IrVar("x")), ir.IrVar("a")])
    other = ir.IrBlock([ir.IrImmutableBind("b", ir.IrVar("x")), ir.IrVar("b")])
    from tests.unit.model_b_slice_c_support import structural_key

    assert structural_key(block, {"x": 0}) == structural_key(other, {"x": 0})


def test_codex_reproducer_rejects_renamed_guard_local_duplicate_and_keeps_group():
    from tests.unit.model_b_slice_c_support import outcome

    result = outcome("f(x) ? { a =: x; a > 0 } = 1\nf(y) ? { b =: y; b > 0 } = 2\nf(1)")
    assert result.error_class == "OpenFunctionDuplicateClauseError"
    assert result.message.startswith("open-function-duplicate-clause: f in unit 'base'")
    # The installed group is unchanged: an earlier-installed clause still answers.
    single = outcome("f(x) ? { a =: x; a > 0 } = 1\nf(1)")
    assert (single.error_class, single.value) == (None, 1)
