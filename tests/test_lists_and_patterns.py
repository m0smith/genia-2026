def test_list_literal(run):
    assert run("[1, 2, 3]") == [1, 2, 3]


def test_recursive_len(run):
    src = '''
    len(xs) =
      [] -> 0 |
      [_, ..rest] -> 1 + len(rest)

    len([10, 20, 30, 40])
    '''
    assert run(src) == 4


def test_rest_pattern_and_wildcard(run):
    src = '''
    head(xs) =
      [x, .._] -> x

    head([9, 8, 7])
    '''
    assert run(src) == 9


def test_list_spread_literal(run):
    assert run("[..[1,2]]") == [1, 2]
    assert run("[1, ..[2,3]]") == [1, 2, 3]
    assert run("[..[1,2], ..[3,4]]") == [1, 2, 3, 4]
    assert run("[0, ..[1,2], 3]") == [0, 1, 2, 3]


def test_list_spread_literal_requires_list(run):
    import pytest

    with pytest.raises(TypeError, match="Cannot spread non-list"):
        run("[..1]")


def test_call_spread_basic(run):
    src = """
    add(a, b) = a + b
    add(..[1, 2])
    """
    assert run(src) == 3


def test_call_spread_mixed(run):
    src = """
    pack(a, b, c, d) = [a, b, c, d]
    pack(0, ..[1, 2], 3)
    """
    assert run(src) == [0, 1, 2, 3]


def test_call_spread_multiple(run):
    src = """
    pack4(a, b, c, d) = [a, b, c, d]
    pack4(..[1, 2], ..[3, 4])
    """
    assert run(src) == [1, 2, 3, 4]


def test_call_spread_empty_list_preserves_arity_behavior(run):
    import pytest

    src = """
    pair(a, b) = [a, b]
    pair(..[], 9)
    """
    with pytest.raises(TypeError, match="No matching function: pair/1"):
        run(src)


def test_call_spread_requires_list(run):
    import pytest

    src = """
    add(a, b) = a + b
    add(..1)
    """
    with pytest.raises(TypeError, match="Cannot spread non-list into function arguments"):
        run(src)


def test_ordinary_call_still_works(run):
    src = """
    add(a, b) = a + b
    add(1, 2)
    """
    assert run(src) == 3
