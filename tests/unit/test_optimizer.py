# Tests for issue #226: extract lowering optimizer into genia.optimizer
#
# All tests that import from genia.optimizer will FAIL before implementation
# because the module does not exist yet.
# Tests that import from genia.interpreter verify backward compatibility.

import pytest

from genia.interpreter import Parser, lex, lower_program


# --- Import contract ---


def test_optimize_program_importable_from_genia_optimizer():
    from genia.optimizer import optimize_program  # noqa: F401


def test_optimize_nth_style_recursion_importable_from_genia_optimizer():
    from genia.optimizer import optimize_nth_style_recursion  # noqa: F401


def test_is_tail_recursive_step_importable_from_genia_optimizer():
    from genia.optimizer import is_tail_recursive_step  # noqa: F401


def test_recursive_call_count_importable_from_genia_optimizer():
    from genia.optimizer import recursive_call_count  # noqa: F401


def test_optimize_program_still_importable_from_genia_interpreter():
    # backward-compatibility re-export must survive the extraction
    from genia.interpreter import optimize_program  # noqa: F401


# --- No import cycle ---


def test_optimizer_does_not_import_interpreter():
    import sys
    import importlib

    # Remove cached module if present so we get a fresh load
    for key in list(sys.modules):
        if key in ("genia.optimizer", "genia.interpreter"):
            del sys.modules[key]

    # Load optimizer without triggering interpreter load
    import genia.optimizer  # noqa: F401

    assert "genia.interpreter" not in sys.modules, (
        "genia.optimizer must not import genia.interpreter"
    )


# --- Behavioral invariants via new import path ---


def test_optimize_program_empty_input_returns_empty_list():
    from genia.optimizer import optimize_program

    result = optimize_program([])
    assert result == []


def test_optimize_program_non_funcdef_nodes_pass_through():
    from genia.optimizer import optimize_program
    from genia.interpreter import IrExprStmt, IrLiteral

    src = "42"
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    result = optimize_program(ir_nodes)
    assert len(result) == 1
    assert isinstance(result[0], IrExprStmt)
    assert isinstance(result[0].expr, IrLiteral)
    assert result[0].expr.value == 42


def test_optimize_program_nth_style_rewritten_to_loop_via_optimizer_import():
    from genia.optimizer import optimize_program
    from genia.interpreter import IrFuncDef, IrListTraversalLoop

    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = optimize_program(lower_program(ast_nodes))
    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert isinstance(fn.body, IrListTraversalLoop)


def test_optimize_program_non_matching_recursion_not_rewritten_via_optimizer_import():
    from genia.optimizer import optimize_program
    from genia.interpreter import IrFuncDef, IrCase

    src = """
    bad(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> 1 + bad(n - 1, rest)
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = optimize_program(lower_program(ast_nodes))
    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert isinstance(fn.body, IrCase)


def test_optimize_program_debug_flag_does_not_raise():
    from genia.optimizer import optimize_program

    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)
    """
    ast_nodes = Parser(lex(src)).parse_program()
    # debug=True should not raise; it prints to stdout
    result = optimize_program(lower_program(ast_nodes), debug=True)
    assert result  # non-empty


# --- Result equivalence: new import == interpreter re-export ---


def test_optimize_program_results_identical_from_both_import_paths():
    from genia.optimizer import optimize_program as opt_from_optimizer
    from genia.interpreter import optimize_program as opt_from_interpreter, IrFuncDef

    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    result_a = opt_from_optimizer(ir_nodes)
    # Re-lower so we get a fresh list (optimize_program consumes an iterable)
    ast_nodes2 = Parser(lex(src)).parse_program()
    ir_nodes2 = lower_program(ast_nodes2)
    result_b = opt_from_interpreter(ir_nodes2)

    assert len(result_a) == len(result_b)
    for a, b in zip(result_a, result_b):
        assert type(a) is type(b)
        if isinstance(a, IrFuncDef):
            assert type(a.body) is type(b.body)
