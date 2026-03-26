from genia.interpreter import (
    IrCase,
    IrFuncDef,
    IrPatBind,
    IrPatList,
    IrPatRest,
    IrPatTuple,
    Parser,
    lex,
    lower_program,
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
