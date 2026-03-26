from genia.interpreter import (
    IrCall,
    IrCase,
    IrFuncDef,
    IrSpread,
    IrListTraversalLoop,
    IrPatBind,
    IrPatList,
    IrPatRest,
    IrPatTuple,
    Parser,
    lex,
    lower_program,
    optimize_program,
)


def test_lowering_makes_case_patterns_explicit():
    src = """
    nth_like(xs) =
      ([x, ..rest]) -> x |
      (_) -> nil
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert isinstance(fn.body, IrCase)

    first = fn.body.clauses[0].pattern
    assert isinstance(first, IrPatTuple)
    assert isinstance(first.items[0], IrPatList)
    assert isinstance(first.items[0].items[0], IrPatBind)
    assert isinstance(first.items[0].items[1], IrPatRest)


def test_ir_execution_preserves_function_case_semantics(run):
    src = """
    head(xs) =
      ([x, .._]) -> x |
      (_) -> nil

    head([10, 20, 30])
    """
    assert run(src) == 10


def test_ir_execution_preserves_lambda_and_named_function_values(run):
    src = """
    apply(f, x) = f(x)
    inc = (n) -> n + 1
    apply(inc, 41)
    """
    assert run(src) == 42


def test_nth_shape_is_rewritten_to_loop_ir():
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


def test_non_matching_recursion_is_not_rewritten():
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


def test_call_spread_lowers_to_ir_spread_arg():
    ast_nodes = Parser(lex("f(..[1, 2])")).parse_program()
    ir_nodes = lower_program(ast_nodes)

    expr_stmt = ir_nodes[0]
    assert isinstance(expr_stmt.expr, IrCall)
    assert isinstance(expr_stmt.expr.args[0], IrSpread)
