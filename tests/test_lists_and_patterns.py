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
