def test_duplicate_binding_list_match_true(run):
    src = """
    same(xs) =
      [x, x] -> true |
      _ -> false

    same([1, 1])
    """
    assert run(src) is True


def test_duplicate_binding_list_match_false(run):
    src = """
    same(xs) =
      [x, x] -> true |
      _ -> false

    same([1, 2])
    """
    assert run(src) is False


def test_duplicate_binding_tuple_match_true(run):
    src = """
    same_pair(a, b) =
      (x, x) -> true |
      (_, _) -> false

    same_pair(7, 7)
    """
    assert run(src) is True


def test_duplicate_binding_tuple_match_false(run):
    src = """
    same_pair(a, b) =
      (x, x) -> true |
      (_, _) -> false

    same_pair(7, 8)
    """
    assert run(src) is False


def test_duplicate_binding_nested_list_match_true(run):
    src = """
    nested(xs) =
      [[x, x], y] -> true |
      _ -> false

    nested([[3, 3], 9])
    """
    assert run(src) is True


def test_duplicate_binding_nested_list_match_false(run):
    src = """
    nested(xs) =
      [[x, x], y] -> true |
      _ -> false

    nested([[3, 4], 9])
    """
    assert run(src) is False
