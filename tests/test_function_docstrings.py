import pytest

from genia.interpreter import FuncDef, Parser, lex
from genia import make_global_env, run_source


def test_parser_captures_named_function_docstring_metadata():
    src = 'inc(x) = "increment by one" x + 1\n'
    ast = Parser(lex(src), source=src, filename="doc.genia").parse_program()
    fn = ast[0]
    assert isinstance(fn, FuncDef)
    assert fn.docstring == "increment by one"


def test_help_displays_function_docstring_and_source_location():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = 'inc(x) = "increment by one" x + 1\nhelp("inc")\n'
    run_source(src, env, filename="doc.genia")
    out = "".join(outputs)
    assert "inc" in out
    assert "arities: 1" in out
    assert "doc: increment by one" in out
    assert "source: doc.genia:1:1" in out


def test_multiple_identical_docstrings_are_allowed():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    echo() = "echo helper" nil
    echo(x) = "echo helper" x
    help("echo")
    """
    run_source(src, env, filename="echo.genia")
    out = "".join(outputs)
    assert "doc: echo helper" in out
    assert "arities: 0, 1" in out


def test_conflicting_docstrings_raise_clear_error():
    env = make_global_env([])
    src = """
    fn() = "first" nil
    fn(x) = "second" x
    """
    with pytest.raises(TypeError, match="Conflicting docstrings for function fn"):
        run_source(src, env)
