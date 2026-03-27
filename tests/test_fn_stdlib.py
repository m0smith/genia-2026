import pytest


def test_apply_autoload_from_fn_stdlib(run):
    src = '''
    add(a, b) = a + b
    apply(add, [20, 22])
    '''
    assert run(src) == 42


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
