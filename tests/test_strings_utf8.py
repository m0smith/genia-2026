import pytest

from genia import make_global_env, run_source


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def _assert_pending_or_equal(src: str, expected):
    try:
        result = _run(src)
    except NameError:
        pytest.xfail(f"pending builtin behavior for: {src}")
    assert result == expected


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
    _assert_pending_or_equal('byte_length("")', 0)
    _assert_pending_or_equal('byte_length("abc")', 3)
    _assert_pending_or_equal('byte_length("é")', 2)
    _assert_pending_or_equal('byte_length("漢")', 3)
    _assert_pending_or_equal('byte_length("🙂")', 4)


def test_basic_string_predicates_and_search_for_ascii_and_unicode():
    _assert_pending_or_equal('contains("café", "fé")', True)
    _assert_pending_or_equal('starts_with("漢字abc", "漢")', True)
    _assert_pending_or_equal('ends_with("hi🙂", "🙂")', True)

    # Minimal model expectation: `find` returns Unicode code-point positions.
    _assert_pending_or_equal('find("naïve", "ï")', 2)
    _assert_pending_or_equal('find("🙂a", "a")', 1)


def test_split_and_split_whitespace_for_ascii_and_unicode():
    _assert_pending_or_equal('split("a,b,c", ",")', ["a", "b", "c"])
    _assert_pending_or_equal('split("é|漢|🙂", "|")', ["é", "漢", "🙂"])
    _assert_pending_or_equal('split_whitespace("a  b\tc\nd")', ["a", "b", "c", "d"])


def test_join_for_ascii_and_unicode_sequences():
    _assert_pending_or_equal('join(",", ["a", "b", "c"])', "a,b,c")
    _assert_pending_or_equal('join(" ", ["🙂", "漢字"])', "🙂 漢字")


def test_trim_variants_for_ascii_and_unicode():
    _assert_pending_or_equal('trim("  hello  ")', "hello")
    _assert_pending_or_equal('trim_start("  hello")', "hello")
    _assert_pending_or_equal('trim_end("hello  ")', "hello")
    _assert_pending_or_equal('trim("  漢字  ")', "漢字")


def test_basic_case_conversion_ascii_only():
    _assert_pending_or_equal('lower("ABC")', "abc")
    _assert_pending_or_equal('upper("abc")', "ABC")


def test_print_displays_string_content_without_quotes():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)

    run_source('print("漢字🙂")', env)

    assert outputs == ["漢字🙂\n"]


# TODO: Add explicit debug/repr string formatting tests if/when the runtime
# exposes a stable repr/display distinction for programmatic assertions.
