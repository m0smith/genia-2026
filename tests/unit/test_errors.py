import pytest


def test_undefined_name(run):
    with pytest.raises(NameError):
        run("unknown_name")


def test_bad_rest_position(run):
    src = '''
    f(xs) =
      [..rest, x] -> x

    f([1,2,3])
    '''
    with pytest.raises(SyntaxError):
        run(src)


def test_case_error_includes_function_and_arity(run):
    src = """
    only_one(x) =
      1 -> 1
    """
    with pytest.raises(RuntimeError, match=r"only_one/1"):
        run(src + "\nonly_one(2)")
