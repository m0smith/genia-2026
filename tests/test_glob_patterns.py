import pytest


def test_glob_star_matches(run):
    src = '''
    classify(s) =
      glob"a*" -> "yes" |
      _ -> "no"

    classify("alpha")
    '''
    assert run(src) == "yes"


def test_glob_question_matches_single_char(run):
    src = '''
    classify(s) =
      glob"a?c" -> "yes" |
      _ -> "no"

    classify("abc")
    '''
    assert run(src) == "yes"


def test_glob_character_class_and_range(run):
    src = '''
    classify(s) =
      glob"file[0-9][abc]" -> "ok" |
      _ -> "no"

    classify("file3b")
    '''
    assert run(src) == "ok"


def test_glob_negated_class(run):
    src = '''
    classify(s) =
      glob"[!a-z]" -> "non-lower" |
      _ -> "other"

    classify("Q")
    '''
    assert run(src) == "non-lower"


def test_glob_escaped_metacharacters(run):
    src = r'''
    classify(s) =
      glob"\*\?\[\]\\" -> "literal" |
      _ -> "no"

    classify("*?[]\\")
    '''
    assert run(src) == "literal"


def test_glob_empty_and_any_string_behavior(run):
    src_empty = '''
    classify(s) =
      glob"" -> "empty" |
      _ -> "no"

    classify("")
    '''
    assert run(src_empty) == "empty"

    src_star = '''
    classify(s) =
      glob"*" -> "any" |
      _ -> "no"

    classify("")
    '''
    assert run(src_star) == "any"


def test_glob_non_string_mismatch(run):
    src = '''
    classify(v) =
      glob"*" -> "string" |
      _ -> "other"

    classify(123)
    '''
    assert run(src) == "other"


def test_glob_malformed_class_error(run):
    src = '''
    classify(s) =
      glob"[a-z" -> "ok" |
      _ -> "no"

    classify("a")
    '''
    with pytest.raises(SyntaxError, match="unterminated character class"):
        run(src)


def test_glob_in_case_expression(run):
    src = '''
    classify(v) {
      "noop"
      glob"*.md" -> "markdown" |
      _ -> "other"
    }

    classify("readme.md")
    '''
    assert run(src) == "markdown"


def test_glob_in_function_definition_case_body(run):
    src = '''
    classify(v) =
      glob"*.md" -> "markdown" |
      _ -> "other"

    classify("readme.md")
    '''
    assert run(src) == "markdown"
