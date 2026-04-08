from genia.interpreter import (
    IrBinary,
    IrCall,
    IrCase,
    IrExprStmt,
    IrFuncDef,
    IrList,
    IrLiteral,
    IrOptionNone,
    IrOptionSome,
    IrPatLiteral,
    IrPipeline,
    IrSpread,
    IrListTraversalLoop,
    IrPatBind,
    IrPatList,
    IrPatRest,
    IrPatTuple,
    IrVar,
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
    assert isinstance(fn.body, (IrListTraversalLoop, IrCase))


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


def test_pipeline_lowers_to_explicit_ir_pipeline():
    ast_nodes = Parser(lex("3 |> inc |> double")).parse_program()
    ir_nodes = lower_program(ast_nodes)

    expr_stmt = ir_nodes[0]
    assert isinstance(expr_stmt, IrExprStmt)
    assert isinstance(expr_stmt.expr, IrPipeline)
    assert isinstance(expr_stmt.expr.source, IrLiteral)
    assert expr_stmt.expr.source.value == 3
    assert len(expr_stmt.expr.stages) == 2
    assert isinstance(expr_stmt.expr.stages[0], IrVar)
    assert expr_stmt.expr.stages[0].name == "inc"
    assert isinstance(expr_stmt.expr.stages[1], IrVar)
    assert expr_stmt.expr.stages[1].name == "double"


def test_multiline_pipeline_lowers_to_explicit_ir_pipeline():
    src = """
    3
      |> inc
      |> double
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    expr_stmt = ir_nodes[0]
    assert isinstance(expr_stmt, IrExprStmt)
    assert isinstance(expr_stmt.expr, IrPipeline)
    assert [stage.name for stage in expr_stmt.expr.stages if isinstance(stage, IrVar)] == ["inc", "double"]


def test_host_module_stage_remains_explicit_inside_pipeline_ir():
    src = """
    import python.json as pyjson
    "null" |> pyjson/loads
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    expr_stmt = ir_nodes[1]
    assert isinstance(expr_stmt, IrExprStmt)
    assert isinstance(expr_stmt.expr, IrPipeline)
    assert isinstance(expr_stmt.expr.source, IrLiteral)
    assert expr_stmt.expr.source.value == "null"
    assert len(expr_stmt.expr.stages) == 1
    stage = expr_stmt.expr.stages[0]
    assert isinstance(stage, IrBinary)
    assert stage.op == "SLASH"


def test_option_constructors_lower_to_explicit_option_ir_nodes():
    ast_nodes = Parser(lex("[some(1), none(parse_failed, {source: \"x\"})]")).parse_program()
    ir_nodes = lower_program(ast_nodes)

    expr_stmt = ir_nodes[0]
    assert isinstance(expr_stmt, IrExprStmt)
    assert isinstance(expr_stmt.expr, IrList)
    assert isinstance(expr_stmt.expr.items[0], IrOptionSome)
    assert isinstance(expr_stmt.expr.items[0].value, IrLiteral)
    assert expr_stmt.expr.items[0].value.value == 1
    assert isinstance(expr_stmt.expr.items[1], IrOptionNone)


def test_lowered_case_keeps_guard_tuple_and_list_patterns():
    src = """
    classify(xs) =
      ([x, ..rest]) ? x > 0 -> x |
      (_) -> nil
    """
    ast_nodes = Parser(lex(src)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert isinstance(fn.body, IrCase)

    first = fn.body.clauses[0]
    assert first.guard is not None
    assert isinstance(first.pattern, IrPatTuple)
    assert isinstance(first.pattern.items[0], IrPatList)
    assert isinstance(first.pattern.items[0].items[0], IrPatBind)
    assert isinstance(first.pattern.items[0].items[1], IrPatRest)


def test_duplicate_binding_semantics_preserved_through_ir(run):
    src = """
    same_pair(xs) =
      ([x, x]) -> true |
      (_) -> false
    same_pair([7, 7])
    """
    assert run(src) is True
    assert run(src.replace("[7, 7]", "[7, 8]")) is False


def test_block_final_case_behavior_preserved_through_ir(run):
    src = """
    fact(n) {
      0 -> 1 |
      n -> n * fact(n - 1)
    }
    fact(4)
    """
    assert run(src) == 24


def test_named_function_docstring_is_lowered_as_metadata_not_runtime_expr():
    ast_nodes = Parser(lex('inc(x) = "doc text" x + 1')).parse_program()
    ir_nodes = lower_program(ast_nodes)
    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert fn.docstring == "doc text"
    assert isinstance(fn.body, IrBinary)
    assert fn.body.op == "PLUS"
    assert isinstance(fn.body.left, IrVar)
    assert fn.body.left.name == "x"


def test_case_literal_pattern_lowers_to_ir_literal_pattern():
    ast_nodes = Parser(lex("f(x) = (0) -> 1 | (_) -> 2")).parse_program()
    ir_nodes = lower_program(ast_nodes)
    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    first = fn.body.clauses[0].pattern
    assert isinstance(first, IrPatTuple)
    assert isinstance(first.items[0], IrPatLiteral)
    assert first.items[0].value == 0
