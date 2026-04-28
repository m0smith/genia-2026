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


def test_pipeline_lifts_some_input_for_ordinary_stages(run):
    src = """
    inc(x) = x + 1
    some?(some(4) |> inc)
    """
    assert run(src) is True


def test_pipeline_lifted_stage_result_wraps_back_into_some(run):
    src = """
    inc(x) = x + 1
    unwrap_or(-1, some(4) |> inc)
    """
    assert run(src) == 5


def test_pipeline_short_circuits_none_input_before_stage(run):
    src = """
    seen = ref(0)
    bump(x) = {
      ref_update(seen, (n) -> n + 1)
      x + 1
    }

    result = none("missing-key", { key: "name" }) |> bump
    [result, ref_get(seen)]
    """
    result = run(src)
    assert result[1] == 0


def test_pipeline_preserves_some_stage_results(run):
    src = """
    inc_opt(x) = some(x + 1)
    double(x) = x * 2
    unwrap_or(-1, 3 |> inc_opt |> double)
    """
    assert run(src) == 8


def test_pipeline_does_not_lift_for_explicit_option_aware_stage(run):
    src = """
    some(9) |> unwrap_or(0)
    """
    assert run(src) == 9


def test_pipeline_short_circuits_when_a_stage_returns_none(run):
    src = """
    seen = ref(0)
    stop(x) = none("parse-error", { source: "stop" })
    bump(x) = {
      ref_update(seen, (n) -> n + 1)
      x + 1
    }

    result = 3 |> stop |> bump
    [result, ref_get(seen)]
    """
    result = run(src)
    assert result[1] == 0


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


def test_pipeline_with_missing_string_projector_key_returns_none(run):
    src = '''
    record = { name: "Matthew", age: 42 }
    none?(record |> "missing")
    '''
    assert run(src) is True


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
    with pytest.raises(TypeError, match=r"pipeline stage 1 failed in Value mode at 2 .*stage received int; pipeline stage expected a callable value, received int"):
        run("1 |> 2")


def test_pipeline_lifts_some_before_non_option_stage(run):
    assert run('unwrap_or(-1, some("42") |> parse_int)') == 42


def test_pipeline_explicit_bridge_error_reports_mode_and_stage(run):
    with pytest.raises(
        TypeError,
        match=r"pipeline stage 1 failed in Explicit bridge mode at collect .*stage received int; collect expected a flow, received int",
    ):
        run("1 |> collect")
