def test_arithmetic_precedence(run):
    assert run("1 + 2 * 3") == 7


def test_boolean_literals(run):
    assert run("true") is True
    assert run("false") is False
    assert run("nil") is None


def test_string_literal(run):
    assert run('"hello"') == "hello"


def test_block_returns_last_expression(run):
    src = '''
    {
      1 + 1
      3 + 4
    }
    '''
    assert run(src) == 7


def test_function_definition_and_call(run):
    src = '''
    square(x) = x * x
    square(5)
    '''
    assert run(src) == 25

def test_duplicate_binding_enforces_equality(run):
    src = """
    same(xs) =
      [x, x] -> true |
      _ -> false

    same([1,1])
    """
    assert run(src) is True

def test_duplicate_binding_mismatch(run):
    src = """
    same(xs) =
      [x, x] -> true |
      _ -> false

    same([1,2])
    """
    assert run(src) is False