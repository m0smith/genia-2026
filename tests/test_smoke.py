def test_multiline_program(run):
    src = """
    add(x, y) = x + y

    result = add(2, 3)
    result
    """
    assert run(src) == 5


def test_reduce_pipeline(run):
    src = """
    reduce(f, acc, xs) =
      (f, acc, []) -> acc |
      (f, acc, [x, ..rest]) -> reduce(f, f(acc, x), rest)

    sum(xs) = reduce((acc, x) -> acc + x, 0, xs)

    sum([1,2,3,4])
    """
    assert run(src) == 10
