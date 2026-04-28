import pytest


def test_varargs_collects_all_args(run):
    src = '''
    list(..xs) = xs
    list()
    '''
    assert run(src) == []

    src = '''
    list(..xs) = xs
    list(1)
    '''
    assert run(src) == [1]

    src = '''
    list(..xs) = xs
    list(1, 2, 3)
    '''
    assert run(src) == [1, 2, 3]


def test_varargs_with_fixed_prefix(run):
    src = '''
    pairPlusRest(a, ..xs) = [a, xs]
    pairPlusRest(1)
    '''
    assert run(src) == [1, []]

    src = '''
    pairPlusRest(a, ..xs) = [a, xs]
    pairPlusRest(1, 2, 3)
    '''
    assert run(src) == [1, [2, 3]]


def test_arity_behavior_preserved(run):
    src = '''
    f(a, b) = a + b
    f(1, 2)
    '''
    assert run(src) == 3

    with pytest.raises(TypeError):
        run(
            '''
            f(a, b) = a + b
            f(1)
            '''
        )

    with pytest.raises(TypeError):
        run(
            '''
            f(a, b) = a + b
            f(1, 2, 3)
            '''
        )

    src = '''
    g(a, ..rest) = a
    g(1, 2, 3)
    '''
    assert run(src) == 1


def test_apply_behavior(run):
    src = '''
    list(..xs) = xs
    apply(list, [])
    '''
    assert run(src) == []

    src = '''
    list(..xs) = xs
    apply(list, [1, 2, 3])
    '''
    assert run(src) == [1, 2, 3]

    src = '''
    add(a, b) = a + b
    apply(add, [2, 3])
    '''
    assert run(src) == 5

    src = '''
    inc(x) = x + 1
    apply(inc, [4])
    '''
    assert run(src) == 5

    with pytest.raises(TypeError):
        run(
            '''
            inc(x) = x + 1
            apply(inc, [])
            '''
        )

    with pytest.raises(TypeError):
        run(
            '''
            inc(x) = x + 1
            apply(inc, [1, 2])
            '''
        )

    with pytest.raises(TypeError):
        run(
            '''
            inc(x) = x + 1
            apply(inc, 42)
            '''
        )


def test_varargs_lambda_and_apply_closure(run):
    src = '''
    list = (..xs) -> xs
    apply(list, [1, [2, 3]])
    '''
    assert run(src) == [1, [2, 3]]

    src = '''
    n = 2
    add2 = (x) -> n + x
    apply(add2, [5])
    '''
    assert run(src) == 7


def test_rest_parameter_must_be_final(run):
    with pytest.raises(SyntaxError):
        run(
            '''
            bad(..xs, y) = y
            bad(1, 2)
            '''
        )
