import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug, utf8_codepoints, utf8_is_boundary, utf8_safe_slice_by_codepoint


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_basic_string_find_absence_reason_remains_structured():
    assert format_debug(_run('absence_reason(find("abc", "x"))')) == 'some("not-found")'


def test_parse_int_rejects_non_string_and_bad_base():
    with pytest.raises(TypeError, match="parse_int expected an integer base"):
        _run('parse_int("10", "2")')
    with pytest.raises(ValueError, match="parse_int expected base in 2..36"):
        _run('parse_int("10", 1)')


def test_parse_int_returns_structured_absence_for_empty_and_invalid_digits():
    assert format_debug(_run('parse_int("   ")')) == 'none("parse-error", {source: "parse_int", expected: "integer_string", received: "   ", base: 10})'
    assert format_debug(_run('parse_int("102", 2)')) == 'none("parse-error", {source: "parse_int", expected: "integer_string", received: "102", base: 2})'


def test_print_displays_string_content_without_quotes():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)

    run_source('print("漢字🙂")', env)

    assert outputs == ["漢字🙂\n"]


def test_debug_format_uses_quoted_escaped_strings():
    assert format_debug("漢字🙂") == '"漢字🙂"'
    assert format_debug("a\n\tb") == r'"a\n\tb"'


def test_utf8_internal_helpers_boundaries_and_slicing_are_safe():
    text = "é漢🙂z"
    assert list(utf8_codepoints(text)) == ["é", "漢", "🙂", "z"]
    assert utf8_is_boundary(text, 0) is True
    assert utf8_is_boundary(text, 1) is False
    assert utf8_is_boundary(text, 2) is True
    assert utf8_is_boundary(text, 5) is True
    assert utf8_is_boundary(text, 8) is False
    assert utf8_is_boundary(text, 9) is True
    assert utf8_safe_slice_by_codepoint(text, 0, 3) == "é漢🙂"
    assert utf8_safe_slice_by_codepoint(text, 1, 3) == "漢🙂"
