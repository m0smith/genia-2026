import pytest

from genia.interpreter import Parser, lex, lower_program, optimize_program
from hosts.python.ir_normalize import normalize_portable_ir


def test_shared_ir_normalization_rejects_host_local_optimized_nodes():
    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)
    """

    ast_nodes = Parser(lex(src)).parse_program()
    optimized = optimize_program(lower_program(ast_nodes))

    with pytest.raises(RuntimeError, match="IrListTraversalLoop appeared before host-local optimization"):
        normalize_portable_ir(optimized)
