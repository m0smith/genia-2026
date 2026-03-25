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
