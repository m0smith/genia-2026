import pytest


def test_pipeline_minimal_call(run):
    src = """
    inc(x) = x + 1
    4 |> inc
    """
    assert run(src) == 5


def test_pipeline_appends_left_value_to_existing_call_args(run):
    src = """
    pair(a, b) = [a, b]
    9 |> pair(1)
    """
    assert run(src) == [1, 9]


def test_pipeline_precedence_with_arithmetic(run):
    src = """
    double(x) = x * 2
    1 + 2 |> double
    """
    assert run(src) == 6


def test_pipeline_is_left_associative(run):
    src = """
    inc(x) = x + 1
    double(x) = x * 2
    3 |> inc |> double
    """
    assert run(src) == 8


def test_pipeline_allows_newline_before_pipe_operator(run):
    src = """
    inc(x) = x + 1
    double(x) = x * 2
    3
      |> inc
      |> double
    """
    assert run(src) == 8


def test_pipeline_allows_newline_after_pipe_operator(run):
    src = """
    inc(x) = x + 1
    double(x) = x * 2
    3 |>
      inc |>
      double
    """
    assert run(src) == 8


def test_pipeline_nested_in_call_argument(run):
    src = """
    inc(x) = x + 1
    identity(x) = x
    identity(1 |> inc)
    """
    assert run(src) == 2


def test_pipeline_with_lambda_rhs(run):
    src = """
    4 |> ((x) -> x * x)
    """
    assert run(src) == 16


def test_pipeline_with_block_rhs(run):
    src = """
    inc(x) = x + 1
    9 |> { inc }
    """
    assert run(src) == 10


def test_pipeline_with_list_helpers(run):
    src = """
    inc(x) = x + 1
    [1, 2, 3] |> map(inc)
    """
    assert run(src) == [2, 3, 4]


def test_pipeline_people_map_name_projector_call_form(run):
    src = '''
    people = [{name: "A"}, {name: "B"}]
    people |> map("name")
    '''
    assert run(src) == ["A", "B"]


def test_pipeline_with_string_projector_rhs(run):
    src = '''
    record = { name: "Matthew", age: 42 }
    record |> "name"
    '''
    assert run(src) == "Matthew"


def test_pipeline_with_missing_string_projector_key_returns_nil(run):
    src = '''
    record = { name: "Matthew", age: 42 }
    record |> "missing"
    '''
    assert run(src) is None


def test_pipeline_with_parenthesized_string_projector_rhs(run):
    src = '''
    record = { name: "Matthew" }
    record |> ("name")
    '''
    assert run(src) == "Matthew"


def test_pipeline_string_projector_chain(run):
    src = '''
    record = { user: { name: "Matthew" } }
    record |> "user" |> "name"
    '''
    assert run(src) == "Matthew"


def test_pipeline_with_case_expression_still_rejected_in_subexpression(run):
    src = """
    id(x) = x
    1 |> id((
      1 -> 2
    ))
    """
    with pytest.raises(SyntaxError):
        run(src)


def test_pipeline_failure_when_rhs_is_not_callable(run):
    with pytest.raises(TypeError):
        run("1 |> 2")
