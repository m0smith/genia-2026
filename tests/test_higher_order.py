def test_named_function_as_value(run):
    src = '''
    add(x, y) = x + y
    apply2(f, a, b) = f(a, b)
    apply2(add, 2, 3)
    '''
    assert run(src) == 5


def test_lambda_reduce_count(run):
    src = '''
    reduce(f, acc, xs) =
      (f, acc, []) -> acc |
      (f, acc, [x, ..rest]) -> reduce(f, f(acc, x), rest)

    count(xs) = reduce((acc, _) -> acc + 1, 0, xs)

    count([1, 2, 3, 4])
    '''
    assert run(src) == 4
