import pytest

from genia.interpreter import (
   
    IrPatBind,
    IrPatMap,
    IrPatTuple,
    Parser,
    make_global_env,
    lex,
    lower_program,
    run_source,
)

from genia.ir import (
    IrExprStmt,
        IrFuncDef,
        IrMap,
)

def test_map_literal_basics_and_identifier_key_sugar(run):
    src = '''
    person = { name: "Matthew", age: 42 }
    [map_get(person, "name"), map_get(person, "age")]
    '''
    assert run(src) == ["Matthew", 42]


def test_empty_map_literal(run):
    assert run("map_count({})") == 0


def test_map_literal_trailing_comma(run):
    assert run('map_get({ name: "m", }, "name")') == "m"


def test_map_literal_string_keys(run):
    assert run('map_get({ "x": 10, "y": 20 }, "y")') == 20


def test_map_literal_duplicate_keys_last_one_wins(run):
    assert run('map_get({ name: "first", name: "second" }, "name")') == "second"


def test_map_patterns_explicit_binding(run):
    src = '''
    greet(person) =
      ({ name: n }) -> "Hello " + n
    greet({ name: "Matthew", age: 42 })
    '''
    assert run(src) == "Hello Matthew"


def test_map_patterns_explicit_string_key_binding(run):
    src = '''
    greet(person) =
      ({ "name": n }) -> "Hello " + n
    greet({ name: "Matthew", age: 42 })
    '''
    assert run(src) == "Hello Matthew"


def test_map_patterns_shorthand_binding(run):
    src = '''
    greet(person) =
      ({ name }) -> "Hello " + name
    greet({ name: "Matthew", age: 42 })
    '''
    assert run(src) == "Hello Matthew"


def test_map_patterns_mixed_shorthand_and_explicit(run):
    src = '''
    describe(person) =
      ({ name, age: years, city }) -> [name, years, city]
    describe({ name: "M", age: 42, city: "SF" })
    '''
    assert run(src) == ["M", 42, "SF"]


def test_map_patterns_partial_matching_semantics(run):
    src = '''
    classify(x) =
      ({ type: "user", name }) -> "user:" + name |
      ({ type: "system" }) -> "system"
    classify({ type: "system", extra: 1 })
    '''
    assert run(src) == "system"


def test_map_patterns_missing_key_mismatch(run):
    src = '''
    classify(x) =
      ({ name }) -> name
    classify({ age: 42 })
    '''
    with pytest.raises(RuntimeError, match="No matching case"):
        run(src)


def test_map_patterns_duplicate_binding_equality_semantics(run):
    src = '''
    same(x) =
      ({ left: n, right: n }) -> true |
      (_) -> false
    [same({ left: 1, right: 1 }), same({ left: 1, right: 2 })]
    '''
    assert run(src) == [True, False]


def test_map_patterns_work_in_function_clauses(run):
    src = '''
    tag(item) =
      ({ type: "user", name }) -> "u:" + name |
      ({ type: "system" }) -> "s"
    tag({ type: "user", name: "a", age: 1 })
    '''
    assert run(src) == "u:a"


def test_map_patterns_work_in_case_expressions(run):
    src = '''
    classify(x) {
      { type: "user", name } -> "user:" + name |
      { type: "system" } -> "system"
    }

    classify({ type: "user", name: "Ada", extra: true })
    '''
    assert run(src) == "user:Ada"


def test_map_patterns_allow_trailing_comma(run):
    src = '''
    classify(x) =
      ({ type: "user", name, }) -> "user:" + name
    classify({ type: "user", name: "Ada" })
    '''
    assert run(src) == "user:Ada"


def test_invalid_map_pattern_string_key_shorthand_is_rejected(run):
    src = '''
    f(x) =
      ({ "name" }) -> x
    '''
    with pytest.raises(SyntaxError, match="shorthand is only allowed for identifier keys"):
        run(src)


def test_ir_contains_map_literal_and_map_pattern_nodes():
    src = '''
    classify(x) =
      ({ name }) -> name
    { name: "m" }
    '''
    ir_nodes = lower_program(Parser(lex(src)).parse_program())

    fn = ir_nodes[0]
    assert isinstance(fn, IrFuncDef)
    assert isinstance(fn.body.clauses[0].pattern, IrPatTuple)
    pat = fn.body.clauses[0].pattern.items[0]
    assert isinstance(pat, IrPatMap)
    assert isinstance(pat.items[0][1], IrPatBind)

    expr_stmt = ir_nodes[1]
    assert isinstance(expr_stmt, IrExprStmt)
    assert isinstance(expr_stmt.expr, IrMap)


def test_map_literal_identifier_and_string_keys_same_result():
    env = make_global_env([])
    left = run_source('map_get({ name: "Matthew" }, "name")', env)
    right = run_source('map_get({ "name": "Matthew" }, "name")', env)
    assert left == right == "Matthew"
