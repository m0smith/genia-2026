"""Python optimizer internals: collection recursion must prevent unsafe rewrites.

Shared R16 evaluation twins assert the portable results; host-local node selection
and syntactic call counting are Python implementation details.
"""
import pytest

from genia.interpreter import Parser, lex, lower_program
from genia.ir import IrCase, IrExprStmt, IrListTraversalLoop
from genia.optimizer import optimize_program, recursive_call_count


@pytest.mark.parametrize('expression', [
    '[f(0), {nested: [f(1)]}]',
    '{first: f(0), nested: [{again: f(1)}]}',
])
def test_recursive_calls_inside_nested_collections_are_counted(expression):
    node = lower_program(Parser(lex(expression)).parse_program())[0]
    assert isinstance(node, IrExprStmt)
    assert recursive_call_count(node.expr, 'f') == 2
    assert recursive_call_count(node.expr, 'other') == 0


@pytest.mark.parametrize('result', ['[nth(0, rest)]', '{value: nth(0, rest)}'])
def test_collection_recursion_in_extra_clause_prevents_nth_rewrite(result):
    source = f'''nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (1, [_, ..rest]) -> {result} |
      (n, [_, ..rest]) -> nth(n - 1, rest)
    '''
    fn = lower_program(Parser(lex(source)).parse_program())[0]
    assert recursive_call_count(fn.body, 'nth') == 2
    assert optimize_program([fn])[0] is fn
    assert isinstance(fn.body, IrCase)
    assert not isinstance(fn.body, IrListTraversalLoop)


def test_quote_does_not_count_as_executable_recursion():
    node = lower_program(Parser(lex('quote(f(0))')).parse_program())[0]
    assert recursive_call_count(node, 'f') == 0
