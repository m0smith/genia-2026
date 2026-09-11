"""Verifies the runnable examples quoted in docs/releases/R19.md are accurate.

Not a general-purpose test; exists so the release doc's small examples stay
truthful if the underlying behavior ever changes.
"""

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_release_doc_no_matching_case_example():
    src = 'f(x) =\n  1 -> "one"\nf("hello")'
    try:
        _run(src)
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert str(e) == 'No matching case for function f/1 with arguments ["hello"]'


def test_release_doc_debug_escape_example():
    assert format_debug("a\x00b\nc\x7fd\x80e") == '"a\\u0000b\\nc\\u007fd\\u0080e"'


def test_release_doc_debug_literal_example():
    assert format_debug("é漢\U0001f600") == '"é漢😀"'
