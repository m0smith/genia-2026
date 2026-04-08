import pytest


def test_apply_autoload_from_fn_stdlib(run):
    src = '''
    add(a, b) = a + b
    apply(add, [20, 22])
    '''
    assert run(src) == 42


def test_autoloaded_fn_helper_can_be_used_as_function_value(run):
    src = """
    unwrap_or([], unwrap_or(none, map_some(rule_emit, some(5))) |> then_get("emit"))
    """
    assert run(src) == [5]


def test_autoloaded_rule_helper_composes_directly_with_option_aware_pipelines_in_rules(run):
    src = """
    rows() = ["a b c d 5 x", "1 2 3 4 6 y", "short"]

    rows() |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> flat_map_some(parse_int) |> flat_map_some(rule_emit)) |> collect
    """
    assert run(src) == [5, 6]


def test_compose_varargs_chain(run):
    src = '''
    add(a, b) = a + b
    inc(x) = x + 1
    square(x) = x * x

    f = compose(square, inc, add)
    f(2, 3)
    '''
    assert run(src) == 36


def test_compose_single_function_passthrough(run):
    src = '''
    pair(a, b) = [a, b]
    f = compose(pair)
    f(1, 2)
    '''
    assert run(src) == [1, 2]


def test_compose_empty_function_list_has_no_matching_clause(run):
    with pytest.raises(RuntimeError):
        run(
            '''
            id = compose()
            id(1)
            '''
        )
