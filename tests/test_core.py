def test_arithmetic_precedence(run):
    assert run("1 + 2 * 3") == 7


def test_boolean_literals(run):
    assert run("true") is True
    assert run("false") is False
    assert run('none?(nil)') is True


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
