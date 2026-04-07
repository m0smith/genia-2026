import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug, utf8_codepoints, utf8_is_boundary, utf8_safe_slice_by_codepoint


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_unicode_string_literals_round_trip_through_parser_and_eval(run):
    assert run('"é"') == "é"
    assert run('"漢字"') == "漢字"
    assert run('"🙂"') == "🙂"
    assert run('"ASCII + 漢字 + 🙂"') == "ASCII + 漢字 + 🙂"


def test_string_literal_escapes_round_trip(run):
    assert run(r'"\n"') == "\n"
    assert run(r'"\r"') == "\r"
    assert run(r'"\t"') == "\t"
    assert run(r'"\\"') == "\\"
    assert run(r'"\""') == '"'
    assert run(r'"\u00E9"') == "é"
    assert run(r'"\u6F22"') == "漢"


def test_byte_length_utf8_minimal_examples():
    assert _run('byte_length("")') == 0
    assert _run('byte_length("abc")') == 3
    assert _run('byte_length("é")') == 2
    assert _run('byte_length("漢")') == 3
    assert _run('byte_length("🙂")') == 4


def test_string_public_wrappers_work_as_function_values():
    assert _run('apply(parse_int, ["42"])') == 42
    assert _run('apply(trim, ["  hello  "])') == "hello"


def test_basic_string_predicates_and_search_for_ascii_and_unicode():
    assert _run('contains("café", "fé")') is True
    assert _run('starts_with("漢字abc", "漢")') is True
    assert _run('ends_with("hi🙂", "🙂")') is True

    # Minimal model expectation: `find` returns maybe-aware Unicode code-point positions.
    assert _run('unwrap_or(-1, find("naïve", "ï"))') == 2
    assert _run('unwrap_or(-1, find("🙂a", "a"))') == 1
    assert _run('is_none?(find("abc", "x"))') is True
    assert format_debug(_run('absence_reason(find("abc", "x"))')) == "some(not_found)"


def test_split_and_split_whitespace_for_ascii_and_unicode():
    assert _run('split("a,b,c", ",")') == ["a", "b", "c"]
    assert _run('split("é|漢|🙂", "|")') == ["é", "漢", "🙂"]
    assert _run('split_whitespace("a  b\tc\nd")') == ["a", "b", "c", "d"]


def test_fields_minimal_awkify_style_split_behavior():
    assert _run('fields("")') == [""]
    assert _run('fields("abc")') == ["abc","abc"]
    assert _run('fields("a b c")') == ["a b c", "a", "b", "c"]
    assert _run('fields("  a   b\tc\nd  ")') == ["  a   b\tc\nd  ","a", "b", "c", "d"]
    assert _run('fields("é 漢 🙂")') == ["é 漢 🙂", "é", "漢", "🙂"]


def test_fields_rejects_non_string_argument():
    with pytest.raises(TypeError, match="expected a string"):
        _run("fields(123)")


def test_join_for_ascii_and_unicode_sequences():
    assert _run('join(",", ["a", "b", "c"])') == "a,b,c"
    assert _run('join(" ", ["🙂", "漢字"])') == "🙂 漢字"


def test_trim_variants_for_ascii_and_unicode():
    assert _run('trim("  hello  ")') == "hello"
    assert _run('trim_start("  hello")') == "hello"
    assert _run('trim_end("hello  ")') == "hello"
    assert _run('trim("  漢字  ")') == "漢字"


def test_basic_case_conversion_ascii_only():
    assert _run('lower("ABC")') == "abc"
    assert _run('upper("abc")') == "ABC"


def test_parse_int_decimal_and_signed_whitespace_cases():
    assert _run('parse_int("42")') == 42
    assert _run('parse_int("  -17  ")') == -17
    assert _run('parse_int("+9")') == 9


def test_parse_int_with_explicit_base():
    assert _run('parse_int("ff", 16)') == 255
    assert _run('parse_int("101010", 2)') == 42
    assert _run('parse_int("z", 36)') == 35


def test_parse_int_rejects_non_string_and_bad_base():
    with pytest.raises(TypeError, match="parse_int expected a string"):
        _run("parse_int(42)")
    with pytest.raises(TypeError, match="parse_int expected an integer base"):
        _run('parse_int("10", "2")')
    with pytest.raises(ValueError, match="parse_int expected base in 2..36"):
        _run('parse_int("10", 1)')


def test_parse_int_rejects_empty_and_invalid_digits():
    with pytest.raises(ValueError, match="parse_int expected a non-empty integer string"):
        _run('parse_int("   ")')
    with pytest.raises(ValueError, match=r"parse_int invalid integer: '12x'"):
        _run('parse_int("12x")')
    with pytest.raises(ValueError, match=r"parse_int invalid integer for base 2: '102'"):
        _run('parse_int("102", 2)')


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
