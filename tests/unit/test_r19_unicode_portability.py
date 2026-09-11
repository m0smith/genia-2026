"""R19 E19-1 shared evidence: portable Unicode/string semantics (U1/U2/U3).

Per docs/design/r19-unicode-diagnostic-portability-contract.md Section 3 and
Section 7. This module exercises the minimum Unicode evidence families
required for an independent host to reproduce the contract without consulting
Python `str` behavior or Python source.
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import (
    format_debug,
    utf8_byte_length,
    utf8_codepoints,
    utf8_is_boundary,
    utf8_safe_slice_by_codepoint,
)


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


# -- U1: code-point iteration and slice-bound normalization -----------------


def test_u1_codepoint_iteration_1_2_3_4_byte_representatives():
    # "A" (1-byte), "é" (2-byte), "漢" (3-byte), "🙂" (4-byte)
    text = "A" + "é" + "漢" + "\U0001f642"
    assert list(utf8_codepoints(text)) == ["A", "é", "漢", "\U0001f642"]
    assert len(list(utf8_codepoints(text))) == 4
    assert utf8_byte_length(text) == 1 + 2 + 3 + 4


@pytest.mark.parametrize(
    "start,end,expected",
    [
        (None, None, "abcdef"),
        (1, 4, "bcd"),
        (-2, None, "ef"),
        (0, 100, "abcdef"),
        (100, 200, ""),
        (4, 2, ""),
        (0, 0, ""),
        (-100, -100, ""),
        (-100, 100, "abcdef"),
    ],
)
def test_u1_slice_bound_normalization_matches_contract_examples(start, end, expected):
    # Exact examples pinned in the approved contract Section 3.3.
    assert utf8_safe_slice_by_codepoint("abcdef", start, end) == expected


def test_u1_slicing_is_by_codepoint_not_by_utf8_byte():
    # "é" is 1 code point / 2 UTF-8 bytes. Code-point slicing must select
    # whole scalars, never split a multi-byte encoding.
    text = "aéb"  # a, é, b
    assert utf8_safe_slice_by_codepoint(text, 0, 2) == "aé"
    assert utf8_safe_slice_by_codepoint(text, 1, 2) == "é"
    assert len(list(utf8_codepoints(text))) == 3
    assert utf8_byte_length(text) == 4  # 1 + 2 + 1


def test_u1_combining_sequence_is_two_codepoints_not_one_grapheme():
    # "e" + COMBINING ACUTE ACCENT (U+0301) is a single user-perceived
    # grapheme but two Unicode scalar values; R19 is scalar-based, not
    # grapheme-based.
    text = "é"
    assert list(utf8_codepoints(text)) == ["e", "́"]
    assert utf8_safe_slice_by_codepoint(text, 0, 1) == "e"
    assert utf8_safe_slice_by_codepoint(text, 1, 2) == "́"


# -- U2: strict UTF-8 boundaries ---------------------------------------------


def test_u2_boundary_at_zero_and_at_byte_length():
    text = "é漢\U0001f642z"  # 2 + 3 + 4 + 1 = 10 bytes
    assert utf8_byte_length(text) == 10
    assert utf8_is_boundary(text, 0) is True
    assert utf8_is_boundary(text, 10) is True


def test_u2_boundary_true_at_valid_interior_scalar_boundary():
    text = "é漢\U0001f642z"
    assert utf8_is_boundary(text, 2) is True  # start of 漢
    assert utf8_is_boundary(text, 5) is True  # start of 🙂
    assert utf8_is_boundary(text, 9) is True  # start of z


def test_u2_boundary_false_at_continuation_byte_position():
    text = "é漢\U0001f642z"
    assert utf8_is_boundary(text, 1) is False  # mid-é
    assert utf8_is_boundary(text, 3) is False  # mid-漢
    assert utf8_is_boundary(text, 6) is False  # mid-🙂


def test_u2_boundary_false_for_negative_or_over_length_offsets():
    text = "abc"
    assert utf8_is_boundary(text, -1) is False
    assert utf8_is_boundary(text, 999) is False


def test_u2_malformed_utf8_decode_fails_deterministically_without_host_wording():
    from genia.builtins import GeniaBytes

    env = make_global_env([])
    env.set("bad", GeniaBytes(b"\xff\xfe"))
    with pytest.raises(ValueError) as exc_info:
        run_source("utf8_decode(bad)", env)
    message = str(exc_info.value)
    # Deterministic Genia-authored message, portable across hosts.
    assert message == "utf8_decode invalid UTF-8 at byte offset 0"
    # No raw CPython codec wording ("codec can't decode", "invalid start
    # byte", etc.) may cross the portable boundary.
    assert "codec" not in message
    assert "0xff" not in message.lower()


def test_u2_malformed_utf8_decode_reports_offset_of_first_bad_byte():
    from genia.builtins import GeniaBytes

    env = make_global_env([])
    # Two valid bytes ("h", "i"), then an invalid continuation byte at
    # offset 2.
    env.set("bad", GeniaBytes(b"hi\x80"))
    with pytest.raises(ValueError, match=r"utf8_decode invalid UTF-8 at byte offset 2"):
        run_source("utf8_decode(bad)", env)


def test_u2_no_u_fffd_replacement_on_malformed_input():
    from genia.builtins import GeniaBytes

    env = make_global_env([])
    env.set("bad", GeniaBytes(b"\xff\xfe"))
    with pytest.raises(ValueError) as exc_info:
        run_source("utf8_decode(bad)", env)
    assert "�" not in str(exc_info.value)


def test_u2_valid_utf8_roundtrips_through_encode_decode():
    assert _run('utf8_decode(utf8_encode("hello 漢字 \U0001f642"))') == "hello 漢字 \U0001f642"


# -- U3: deterministic debug escaping ----------------------------------------


def test_u3_short_escapes():
    assert format_debug("\\") == '"\\\\"'
    assert format_debug('"') == '"\\""'
    assert format_debug("\n") == '"\\n"'
    assert format_debug("\r") == '"\\r"'
    assert format_debug("\t") == '"\\t"'


def test_u3_remaining_c0_controls_render_as_lowercase_u_escape():
    # U+0000 (NUL) and U+000B (VT) are C0 controls with no short escape.
    assert format_debug("\x00") == '"\\u0000"'
    assert format_debug("\x0b") == '"\\u000b"'
    assert format_debug("\x1f") == '"\\u001f"'


def test_u3_del_renders_as_u_escape():
    assert format_debug("\x7f") == '"\\u007f"'


def test_u3_c1_controls_render_as_u_escape():
    assert format_debug("\x80") == '"\\u0080"'
    assert format_debug("\x9f") == '"\\u009f"'


def test_u3_other_unicode_scalars_render_literally():
    assert format_debug("é漢\U0001f642") == '"é漢\U0001f642"'


def test_u3_display_has_no_surrounding_quotes_and_no_escaping():
    from genia._format_engine import format_display

    assert format_display("漢字\U0001f642") == "漢字\U0001f642"


def test_u3_mixed_string_debug_rendering():
    text = "a\x00b\nc\x7fd\x80e"
    assert format_debug(text) == '"a\\u0000b\\nc\\u007fd\\u0080e"'
