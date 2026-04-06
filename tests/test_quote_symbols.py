import pytest

from genia import make_global_env, run_source
from genia.interpreter import _main
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_quote_symbol_identity(run):
    assert run("quote(x) == quote(x)") is True


def test_quote_symbol_is_distinct_from_string(run):
    assert run('quote(x) != "x"') is True


def test_quote_nested_lists_preserve_symbols_and_structure():
    result = _run("quote([a, [b, c]])")
    assert format_debug(result) == "(a (b c))"


def test_quote_does_not_evaluate_binary_expressions(run):
    assert run("quote(1 + 2) != 3") is True
    assert format_debug(_run("quote(1 + 2)")) == "(app + 1 2)"


def test_quote_call_represents_program_as_data():
    assert format_debug(_run("quote(add(1, x))")) == "(app add 1 x)"


def test_quote_preserves_identifier_and_string_map_keys():
    src = """
    q = quote({a: 1, "b": c})
    [map_get(q, quote(a)), map_get(q, "b")]
    """
    assert format_debug(_run(src)) == '[1, c]'


def test_quote_of_none_preserves_option_none_literal(run):
    assert run("quote(none) == none") is True


def test_quote_of_structured_none_preserves_absence_metadata():
    assert format_debug(_run("quote(none(empty_list))")) == "none(empty_list)"


def test_quote_of_too_many_arguments_is_rejected():
    with pytest.raises(SyntaxError, match="quote\\(\\.\\.\\.\\) expects exactly one argument"):
        _run("quote(a, b)")


def test_quote_preserves_spread_syntax_as_data():
    assert format_debug(_run("quote([..xs])")) == "((spread xs))"


def test_command_mode_prints_symbols_without_string_quotes(capsys):
    exit_code = _main(["-c", "quote(x)"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "x"
    assert captured.err == ""
