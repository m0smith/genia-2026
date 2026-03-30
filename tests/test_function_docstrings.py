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
    assert "inc/1" in out
    assert "Defined at doc.genia:1" in out
    assert "increment by one" in out


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
    assert "echo/0, 1" in out
    assert "echo helper" in out


def test_conflicting_docstrings_raise_clear_error():
    env = make_global_env([])
    src = """
    fn() = "first" nil
    fn(x) = "second" x
    """
    with pytest.raises(TypeError, match="Conflicting docstrings for function fn"):
        run_source(src, env)


def test_help_renders_markdown_docstring_with_normalized_whitespace():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    sum(xs) = "# sum\\n\\nReturn total from `xs`.\\n\\n## Params\\n- xs: numbers\\n\\n\\n\\n## Examples\\n```genia\\nsum([]) -> 0\\n```" 0
    help("sum")
    """
    run_source(src, env, filename="sum.genia")
    out = "".join(outputs)
    assert "sum/1" in out
    assert "# sum" in out
    assert "Return total from `xs`." in out
    assert "## Params" in out
    assert "- xs: numbers" in out
    assert "```genia" in out
    assert "sum([]) -> 0" in out
    assert "\n\n\n" not in out


def test_help_undocumented_function_fallback():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source("sum(xs) = 0\nhelp(\"sum\")\n", env, filename="sum.genia")
    out = "".join(outputs)
    assert "sum/1" in out
    assert "No documentation available." in out


def test_help_docstring_normalizes_triple_quote_wrappers_and_indentation():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = r'''
    sum(xs) = "\"\"\"\n        # sum\n\n          - xs: list of numbers\n    \"\"\"" 0
    help("sum")
    '''
    run_source(src, env, filename="sum.genia")
    out = "".join(outputs)
    assert "# sum" in out
    assert "- xs: list of numbers" in out


def test_triple_quoted_multiline_docstring_source_is_supported():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = '''
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    help("inc")
    '''
    run_source(src, env, filename="inc.genia")
    out = "".join(outputs)
    assert "# inc" in out
    assert "Increment by one." in out
