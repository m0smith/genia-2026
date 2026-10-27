"""Slice C GREEN repair R2 (#1269, PR #1270): guard-local lexical normalization.

PYTHON REFERENCE HOST ONLY. Immutable declarations inside guard blocks introduce
lexical binders: the initializer is keyed under the bindings visible before the
declaration, the binder enters scope afterwards, shadowing is honoured, free
references stay syntactically distinct, and block scopes end with the block.
"""

from __future__ import annotations

import pytest

from genia import ir
from genia.pattern_match import IrPatBind, IrPatTuple
from genia.structural_key import open_dispatch_key
from genia.interpreter import Parser, lex, lower_program
from tests.unit.model_b_slice_c_support import dispatch_key


def key(text: str) -> tuple:
    """Dispatch key of the first clause of the `open` declaration `text`."""
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


def test_keying_does_not_execute_initializers_or_annotations(monkeypatch):
    """The trap is installed on the evaluator itself, so any evaluation during keying fails the test."""
    from genia import evaluator as evaluator_module

    calls: list[str] = []

    def trap(self, *args, **kwargs):
        """Stand-in for an Evaluator method: records the call and fails the test, proving key derivation never evaluates IR."""
        calls.append("evaluated")
        raise AssertionError("key generation must not evaluate IR")

    for name in ("eval", "eval_tail", "eval_call", "eval_annotations", "eval_immutable_bind"):
        if hasattr(evaluator_module.Evaluator, name):
            monkeypatch.setattr(evaluator_module.Evaluator, name, trap)
    guard = ir.IrBlock(
        [
            ir.IrImmutableBind(
                "a",
                ir.IrCall(ir.IrVar("boom"), [ir.IrVar("x")]),
                annotations=[ir.IrAnnotation("meta", ir.IrCall(ir.IrVar("boom"), [ir.IrVar("a")]))],
            ),
            ir.IrLiteral(True),
        ]
    )
    assert open_dispatch_key(IrPatTuple([IrPatBind("x")]), guard) is not None
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


# --- R2-A: declaration-owned annotations see the declared binder ----------------------------


def _annotated_guard(local: str, reference: str, init: str = "x") -> ir.IrBlock:
    """Guard block that declares `local` (initialized from `init`) with a `meta` annotation referencing `reference`, then yields true."""
    return ir.IrBlock(
        [
            ir.IrImmutableBind(
                local,
                ir.IrVar(init),
                annotations=[ir.IrAnnotation("meta", ir.IrMap([("v", ir.IrVar(reference))]))],
            ),
            ir.IrLiteral(True),
        ]
    )


PAT = IrPatTuple([IrPatBind("x")])


def _k(guard):
    """Dispatch key of pattern `PAT` with the given guard."""
    return open_dispatch_key(PAT, guard)


def test_annotation_self_reference_is_alpha_equivalent():
    assert _k(_annotated_guard("a", "a")) == _k(_annotated_guard("b", "b"))


def test_annotation_bound_versus_free_reference_is_distinct():
    assert _k(_annotated_guard("a", "a")) != _k(_annotated_guard("b", "a"))
    assert _k(_annotated_guard("a", "zed")) != _k(_annotated_guard("a", "a"))
    assert _k(_annotated_guard("a", "zed")) == _k(_annotated_guard("b", "zed"))


def test_annotation_reference_to_header_variable_stays_header_bound():
    assert _k(_annotated_guard("a", "x")) == _k(_annotated_guard("b", "x"))
    assert _k(_annotated_guard("a", "x")) != _k(_annotated_guard("a", "a"))


def test_sequential_annotated_declarations():
    def two(first: str, second: str, ref: str) -> ir.IrBlock:
        """Guard block with two annotated declarations: `first` annotated with itself, `second` initialized from `first` and annotated with `ref`."""
        return ir.IrBlock(
            [
                ir.IrImmutableBind(first, ir.IrVar("x"), annotations=[ir.IrAnnotation("meta", ir.IrVar(first))]),
                ir.IrImmutableBind(second, ir.IrVar(first), annotations=[ir.IrAnnotation("meta", ir.IrVar(ref))]),
                ir.IrLiteral(True),
            ]
        )

    assert _k(two("a", "b", "b")) == _k(two("c", "d", "d"))
    assert _k(two("a", "b", "a")) == _k(two("c", "d", "c"))
    assert _k(two("a", "b", "a")) != _k(two("a", "b", "b"))


def test_annotation_shadowing_and_scope_restoration():
    shadow = ir.IrBlock(
        [ir.IrImmutableBind("x", ir.IrLiteral(1), annotations=[ir.IrAnnotation("meta", ir.IrVar("x"))]), ir.IrLiteral(True)]
    )
    renamed = ir.IrBlock(
        [ir.IrImmutableBind("q", ir.IrLiteral(1), annotations=[ir.IrAnnotation("meta", ir.IrVar("q"))]), ir.IrLiteral(True)]
    )
    assert _k(shadow) == _k(renamed)
    # after the block the annotation binder is out of scope again: a trailing `a` is free.
    def after(trailing: str) -> ir.IrBlock:
        """Block holding the annotated guard followed by a reference to `trailing`, which is free once the inner block has ended."""
        return ir.IrBlock([_annotated_guard("a", "a"), ir.IrVar(trailing)])

    assert _k(after("a")) == _k(after("a"))
    assert _k(after("a")) != _k(ir.IrBlock([_annotated_guard("a", "a"), ir.IrVar("x")]))


def _install(env, evaluator, guard, body_value):
    """Evaluate a pattern function definition for `g` with `PAT`, `guard` and a literal body; returns the evaluation result."""
    node = ir.IrPatternFuncDef("g", PAT, guard, ir.IrLiteral(body_value))
    return evaluator.eval(node)


def test_direct_ir_duplicate_installation_matches_key_classification():
    from genia.evaluator import Evaluator
    from genia.pattern_match import IrPatTuple as _T  # noqa: F401
    from tests.unit.model_b_slice_c_support import fresh_env

    env, _ = fresh_env()
    ev = Evaluator(env)
    ev.eval(ir.IrPatternFuncDef("g", PAT, _annotated_guard("a", "a"), ir.IrLiteral(1)))
    group = env.get("g")
    before = list(group.records)
    # alpha-equivalent annotated local: duplicate
    with pytest.raises(Exception, match="open-function-duplicate-clause"):
        ev.eval(ir.IrPatternFuncDef("g", PAT, _annotated_guard("b", "b"), ir.IrLiteral(2)))
    assert env.get("g") is group and group.records == before
    # local-versus-free: a different clause, accepted
    ev.eval(ir.IrPatternFuncDef("g", PAT, _annotated_guard("b", "a"), ir.IrLiteral(3)))
    assert len(group.records) == 2


def test_annotation_effects_distinguish_bound_from_free_references():
    from genia.evaluator import Evaluator
    import genia
    from tests.unit.model_b_slice_c_support import fresh_env

    def run(local_a: str, ref_a: str, local_b: str, ref_b: str):
        """Declare two annotated pattern clauses of `g` and call `g(1)`; returns `(per-clause 'installed' or exception class name, printed annotation effects)`."""
        env, printed = fresh_env()
        genia.run_source("record = (v) -> { print(v); {} }\na = -1", env, filename="<command>")

        def guard(local, ref):
            """Guard block that declares `local` from `x` with a `meta` annotation calling `record(ref)`."""
            return ir.IrBlock(
                [
                    ir.IrImmutableBind(local, ir.IrVar("x"), annotations=[ir.IrAnnotation("meta", ir.IrCall(ir.IrVar("record"), [ir.IrVar(ref)]))]),
                    ir.IrLiteral(True),
                ]
            )

        ev = Evaluator(env)
        outcomes = []
        for local, ref, body in ((local_a, ref_a, 1), (local_b, ref_b, 2)):
            try:
                ev.eval(ir.IrPatternFuncDef("g", PAT, guard(local, ref), ir.IrLiteral(body)))
                outcomes.append("installed")
            except Exception as error:  # noqa: BLE001
                outcomes.append(type(error).__name__)
        env.get("g")(1)
        return outcomes, printed

    # alpha-equivalent: second is a duplicate, so exactly one clause runs; effect sees the local (1).
    assert run("a", "a", "b", "b")[0][1] == "OpenFunctionDuplicateClauseError"
    # bound-versus-free: both install; the first clause (local ref) wins and records 1.
    outcomes, seen = run("a", "a", "b", "a")
    assert outcomes == ["installed", "installed"]
    assert seen[0].strip() == "1"
