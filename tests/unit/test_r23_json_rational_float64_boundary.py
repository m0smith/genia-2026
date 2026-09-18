"""Failing tests for issue #921 (E23-4): strict generic JSON boundary for
Rational and Float64.

Implements docs/design/r23-numeric-representation-interchange-contract.md
sections 4.3 (Rational), 4.4 (Float64), 5 (decode -- confirms Rational/
Float64 stay unreachable from JSON decode), and 8 (diagnostics, this
slice's new rejections) against the strict generic JSON boundary
(`json_decode`/`json_encode`, i.e. `_json_decode`/`_json_encode` in
`src/genia/builtins.py`) -- never the compatibility `json_parse`/
`json_stringify` surface, which is untouched (E23-5).

Out of scope here (later R23 slices): a full diagnostics sweep (E23-6);
release audit (E23-7). E23-3's Integer/Decimal boundary is unchanged and
covered by tests/unit/test_r23_json_integer_decimal_boundary.py.
"""
from __future__ import annotations

import math

import pytest

from src.genia import make_global_env, run_source
from src.genia.equality import genia_equal
from src.genia.numeric_runtime import (
    GeniaDecimal,
    format_float64,
    rational_from_integers,
    rational_terminating_decimal,
    stable_json_decimal,
)
from src.genia.utf8 import format_debug
from src.genia.values import GeniaOptionErr, GeniaOptionSome


def _env():
    return make_global_env([])


def _run(src: str):
    return run_source(src, make_global_env())


def _decode(text_or_bytes):
    return _env().get("_json_decode")(text_or_bytes)


def _encode(value):
    return _env().get("_json_encode")(value)


# ---------------------------------------------------------------------------
# section 4.3 + unit-level: rational_terminating_decimal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (1, 2, GeniaDecimal(5, -1)),  # 0.5
        (1, 4, GeniaDecimal(25, -2)),  # 0.25
        (3, 8, GeniaDecimal(375, -3)),  # 0.375
        (7, 20, GeniaDecimal(35, -2)),  # 0.35
        (-1, 2, GeniaDecimal(-5, -1)),  # -0.5
        (1, 5, GeniaDecimal(2, -1)),  # 0.2
        (1, 10, GeniaDecimal(1, -1)),  # 0.1
    ],
)
def test_rational_terminating_decimal_exact_for_2_5_only_denominators(
    numerator, denominator, expected
):
    value = rational_from_integers(numerator, denominator)
    decimal = rational_terminating_decimal(value)
    assert decimal == expected


@pytest.mark.parametrize("numerator,denominator", [(1, 3), (2, 7), (1, 6), (5, 12)])
def test_rational_terminating_decimal_none_when_denominator_has_other_prime_factors(
    numerator, denominator
):
    # 6 == 2*3 and 12 == 4*3 both still carry a factor of 2, but the
    # surviving factor of 3 makes the expansion non-terminating -- the
    # "only 2/5" test must reject these, not just "has a factor of 2/5".
    value = rational_from_integers(numerator, denominator)
    assert rational_terminating_decimal(value) is None


def test_rational_terminating_decimal_large_prime_denominator_is_none():
    # Denominator with a large prime factor that is not 2 or 5.
    value = rational_from_integers(1, 97)
    assert rational_terminating_decimal(value) is None


def test_rational_terminating_decimal_no_float_cast_in_source():
    import ast
    import inspect

    from src.genia import numeric_runtime

    source = inspect.getsource(numeric_runtime.rational_terminating_decimal)
    tree = ast.parse(source)
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "float" not in call_names


# ---------------------------------------------------------------------------
# encode: terminating Rational -> exact JSON number
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "numerator,denominator,expected_text",
    [
        (1, 2, "0.5"),
        (1, 4, "0.25"),
        (3, 8, "0.375"),
        (7, 20, "0.35"),
    ],
)
def test_encode_terminating_rational_emits_correct_decimal_text(
    numerator, denominator, expected_text
):
    value = rational_from_integers(numerator, denominator)
    result = _encode(value)
    assert isinstance(result, GeniaOptionSome)
    assert result.value == expected_text
    assert '"' not in result.value  # bare number, not a quoted string


@pytest.mark.parametrize("numerator,denominator", [(1, 3), (2, 7)])
def test_encode_non_terminating_rational_rejected_with_normalized_diagnostic(
    numerator, denominator
):
    value = rational_from_integers(numerator, denominator)
    result = _encode(value)
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "unsupported_json_value"


def test_encode_terminating_but_unstable_rational_rejected_with_range_diagnostic():
    # Denominator is a pure power of 5 (5**22), so the expansion
    # terminates, but the resulting Decimal has far more significant
    # digits than binary64 round-trip precision can preserve -- it fails
    # `stable_json_decimal` exactly like an equivalent unstable Decimal
    # literal would (see test_r23_json_integer_decimal_boundary.py).
    denominator = 5**22
    numerator = 10**21 + 1  # deliberately not a multiple that cancels evenly
    value = rational_from_integers(numerator, denominator)
    decimal_equivalent = rational_terminating_decimal(value)
    assert decimal_equivalent is not None
    assert stable_json_decimal(decimal_equivalent) is False

    result = _encode(value)
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


# ---------------------------------------------------------------------------
# decode: JSON never directly constructs a Rational
# ---------------------------------------------------------------------------


def test_decode_encoded_rational_form_yields_decimal_not_rational():
    value = rational_from_integers(1, 4)
    encoded = _encode(value)
    assert isinstance(encoded, GeniaOptionSome)
    decoded = _decode(encoded.value)
    assert isinstance(decoded, GeniaOptionSome)
    result_value = decoded.value.value
    assert isinstance(result_value, GeniaDecimal)
    assert result_value == GeniaDecimal(25, -2)


def test_round_trip_terminating_rational_mathematically_equal_via_r18_equality():
    value = rational_from_integers(3, 8)
    encoded = _encode(value)
    assert isinstance(encoded, GeniaOptionSome)
    decoded = _decode(encoded.value)
    assert isinstance(decoded, GeniaOptionSome)
    result_value = decoded.value.value
    assert isinstance(result_value, GeniaDecimal)
    # R22's "mathematical cross-kind equality" (R18 equality integration):
    # a Decimal and a mathematically-equal Rational compare equal.
    assert genia_equal(result_value, value) is True


# ---------------------------------------------------------------------------
# section 4.4: Float64 encode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [0.1, 4.0, 1e21, 1e-21, -0.0, 0.0, -123.456],
)
def test_encode_finite_float64_matches_canonical_shortest_roundtrip_text(value):
    result = _encode(value)
    assert isinstance(result, GeniaOptionSome)
    canonical = format_float64(value)
    assert canonical.startswith("float64(")
    inner = canonical[len("float64(") : -1]
    assert result.value == inner
    assert "float64(" not in result.value


def test_encode_very_large_float64_uses_scientific_notation_and_matches_format_float64():
    value = 1.23456789e30
    result = _encode(value)
    assert isinstance(result, GeniaOptionSome)
    canonical = format_float64(value)[len("float64(") : -1]
    assert result.value == canonical
    assert "e" in result.value


def test_encode_very_small_float64_uses_scientific_notation_and_matches_format_float64():
    value = 1.23456789e-30
    result = _encode(value)
    assert isinstance(result, GeniaOptionSome)
    canonical = format_float64(value)[len("float64(") : -1]
    assert result.value == canonical
    assert "e" in result.value


def test_encode_signed_zero_float64_preserves_sign_in_text():
    positive = _encode(0.0)
    negative = _encode(-0.0)
    assert isinstance(positive, GeniaOptionSome)
    assert isinstance(negative, GeniaOptionSome)
    assert positive.value == "0.0"
    assert negative.value == "-0.0"


def test_encode_nan_float64_rejected_with_normalized_diagnostic():
    result = _encode(float("nan"))
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_positive_infinity_float64_rejected_with_normalized_diagnostic():
    result = _encode(float("inf"))
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_negative_infinity_float64_rejected_with_normalized_diagnostic():
    result = _encode(float("-inf"))
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_float64_never_raises_raw_valueerror():
    # allow_nan=False on json.dumps would raise a raw ValueError if a
    # non-finite float ever reached it unguarded; the boundary must
    # normalize this before json.dumps is invoked.
    for value in (float("nan"), float("inf"), float("-inf")):
        result = _encode(value)
        assert isinstance(result, GeniaOptionErr)


def test_encode_float64_does_not_use_python_float_repr_directly():
    # Python's own `repr(float)` uses "1e+21" for this magnitude; the
    # canonical R23 rendering rule differs only in edge cases from CPython
    # repr, but this test locks that the boundary goes through
    # `format_float64`'s shared computation rather than `json.dumps`'s
    # own float serialization, which the implementation could otherwise
    # take as a shortcut.
    value = 1e16
    result = _encode(value)
    assert isinstance(result, GeniaOptionSome)
    canonical = format_float64(value)[len("float64(") : -1]
    assert result.value == canonical


# ---------------------------------------------------------------------------
# section 5: Float64 decode -- confirm JSON decode never produces Float64
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("token", ["0.1", "1.5e3", "-0.5", "1e21", "1e-21"])
def test_decode_fraction_exponent_tokens_produce_decimal_never_float(token):
    result = _decode(token)
    assert isinstance(result, GeniaOptionSome)
    value = result.value.value
    assert isinstance(value, GeniaDecimal)
    assert not isinstance(value, float)


def test_decode_encoded_float64_yields_decimal_not_float(*, _v=0.1):
    result = _encode(_v)
    assert isinstance(result, GeniaOptionSome)
    decoded = _decode(result.value)
    assert isinstance(decoded, GeniaOptionSome)
    value = decoded.value.value
    assert isinstance(value, GeniaDecimal)
    assert not isinstance(value, float)


# ---------------------------------------------------------------------------
# nested containers / full Genia source
# ---------------------------------------------------------------------------


def test_genia_source_rejects_non_terminating_rational_via_division():
    # `1 / 3` in Genia produces an exact Rational (E22-4); encoding it must
    # be rejected rather than silently rounded.
    src = "json_encode(1 / 3)"
    result = _run(src)
    rendered = format_debug(result)
    assert "err(" in rendered
    assert "unsupported_json_value" in rendered


def test_genia_source_encodes_terminating_rational_via_division():
    src = 'unwrap_or("", json_encode(1 / 4))'
    result = _run(src)
    rendered = format_debug(result)
    assert "0.25" in rendered
