from genia.interpreter import lex


def _kinds_texts(src: str) -> list[tuple[str, str]]:
    return [(t.kind, t.text) for t in lex(src) if t.kind != "EOF"]


def test_name_suffix_qmark_and_bang_are_plain_identifiers():
    tokens = _kinds_texts("ready? = true\nsave! = false")
    assert tokens == [
        ("IDENT", "ready?"),
        ("ASSIGN", "="),
        ("IDENT", "true"),
        ("NEWLINE", "\n"),
        ("IDENT", "save!"),
        ("ASSIGN", "="),
        ("IDENT", "false"),
    ]


def test_plus_and_slash_are_operators_but_hyphenated_names_are_identifiers():
    tokens = _kinds_texts("foo-bar + a+b + ns/name")
    assert tokens == [
        ("IDENT", "foo-bar"),
        ("PLUS", "+"),
        ("IDENT", "a"),
        ("PLUS", "+"),
        ("IDENT", "b"),
        ("PLUS", "+"),
        ("IDENT", "ns"),
        ("SLASH", "/"),
        ("IDENT", "name"),
    ]
