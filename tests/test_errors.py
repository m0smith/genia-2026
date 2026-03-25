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
