import pytest


def test_varargs_list_empty(run):
    src = """
    list(..xs) = xs
    list()
    """
    assert run(src) == []


def test_varargs_list_one(run):
    src = """
    list(..xs) = xs
    list(1)
    """
    assert run(src) == [1]


def test_varargs_list_many(run):
    src = """
    list(..xs) = xs
    list(1, 2, 3)
    """
    assert run(src) == [1, 2, 3]


def test_varargs_with_fixed_prefix_empty_tail(run):
    src = """
    pairPlusRest(a, ..xs) = [a, xs]
    pairPlusRest(1)
    """
    assert run(src) == [1, []]


def test_varargs_with_fixed_prefix_nonempty_tail(run):
    src = """
    pairPlusRest(a, ..xs) = [a, xs]
    pairPlusRest(1, 2, 3)
    """
    assert run(src) == [1, [2, 3]]


def test_fixed_arity_success(run):
    src = """
    f(a, b) = a + b
    f(1, 2)
    """
    assert run(src) == 3


def test_fixed_arity_too_few_errors(run):
    src = """
    f(a, b) = a + b
    f(1)
    """
    with pytest.raises(TypeError):
        run(src)


def test_fixed_arity_too_many_errors(run):
    src = """
    f(a, b) = a + b
    f(1, 2, 3)
    """
    with pytest.raises(TypeError):
        run(src)


def test_varargs_accepts_extra_args(run):
    src = """
    g(a, ..rest) = a
    g(1, 2, 3)
    """
    assert run(src) == 1


def test_apply_list_empty(run):
    src = """
    list(..xs) = xs
    apply(list, [])
    """
    assert run(src) == []


def test_apply_list_many(run):
    src = """
    list(..xs) = xs
    apply(list, [1, 2, 3])
    """
    assert run(src) == [1, 2, 3]


def test_apply_add(run):
    src = """
    add(a, b) = a + b
    apply(add, [2, 3])
    """
    assert run(src) == 5


def test_apply_inc(run):
    src = """
    inc(x) = x + 1
    apply(inc, [4])
    """
    assert run(src) == 5


def test_apply_inc_too_few_errors(run):
    src = """
    inc(x) = x + 1
    apply(inc, [])
    """
    with pytest.raises(TypeError):
        run(src)


def test_apply_inc_too_many_errors(run):
    src = """
    inc(x) = x + 1
    apply(inc, [1, 2])
    """
    with pytest.raises(TypeError):
        run(src)


def test_apply_requires_list(run):
    src = """
    inc(x) = x + 1
    apply(inc, 42)
    """
    with pytest.raises(TypeError):
        run(src)


def test_varargs_lambda(run):
    assert run("((a, ..rest) -> [a, rest])(1, 2, 3)") == [1, [2, 3]]


def test_apply_closure(run):
    src = """
    addn = (n) -> ((x) -> x + n)
    apply(addn(3), [4])
    """
    assert run(src) == 7


def test_varargs_must_be_final(run):
    with pytest.raises(SyntaxError):
        run("bad(..rest, x) = x")
