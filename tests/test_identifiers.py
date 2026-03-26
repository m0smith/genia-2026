import pytest

from genia.interpreter import lex


def _kinds_texts(src: str) -> list[tuple[str, str]]:
    return [(t.kind, t.text) for t in lex(src) if t.kind != "EOF"]


def test_clojure_style_suffix_names_are_identifiers():
    tokens = _kinds_texts("empty? = true\nupdate! = false")
    assert tokens == [
        ("IDENT", "empty?"),
        ("ASSIGN", "="),
        ("IDENT", "true"),
        ("NEWLINE", "\n"),
        ("IDENT", "update!"),
        ("ASSIGN", "="),
        ("IDENT", "false"),
    ]


def test_arrow_sequence_is_not_allowed_inside_identifier():
    tokens = _kinds_texts("map->vec")
    assert tokens == [
        ("IDENT", "map"),
        ("ARROW", "->"),
        ("IDENT", "vec"),
    ]


def test_unicode_identifiers_are_rejected(run):
    with pytest.raises(SyntaxError, match="Unexpected character"):
        run("naïve = 1")


@pytest.mark.parametrize("src", ["😀 = 1", "😀(x) = x\\n😀(1)", "v😀 = 1"])
def test_emoji_identifiers_and_function_names_are_rejected(src, run):
    with pytest.raises(SyntaxError, match="Unexpected character"):
        run(src)


@pytest.mark.parametrize("src", ["foo+bar = 1", "foo/bar = 1", "foo@bar = 1"])
def test_prohibited_delimiters_and_operators_in_names_fail(src, run):
    with pytest.raises(SyntaxError):
        run(src)


def test_identifier_regression_for_underscore_and_reserved_literals(run):
    src = """
    _ = 10
    a = true
    b = false
    c = nil
    _ + 1
    """
    assert run(src) == 11


def test_arithmetic_operator_tokens_regression():
    tokens = _kinds_texts("a+b-c*d/e%f")
    assert tokens == [
        ("IDENT", "a"),
        ("PLUS", "+"),
        ("IDENT", "b"),
        ("MINUS", "-"),
        ("IDENT", "c"),
        ("STAR", "*"),
        ("IDENT", "d"),
        ("SLASH", "/"),
        ("IDENT", "e"),
        ("PERCENT", "%"),
        ("IDENT", "f"),
    ]
